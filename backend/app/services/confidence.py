"""Composite per-field confidence.

composite = 0.5 * self_reported (from the LLM) + 0.5 * heuristic_score
(format validity, cross-field reconciliation). Fields marked not_applicable
are excluded entirely rather than penalized — a genuinely absent field
shouldn't lower a document's confidence the way a failed extraction should.

Schema-agnostic: works on any ExtractionMeta subclass (InvoiceExtraction,
ResumeExtraction, ...). The two reconciliation checks below are
invoice-specific and simply never fire for a schema without those field
names (guarded with getattr, not a hard dependency on InvoiceExtraction).
"""

from pydantic import BaseModel

from app.core.config import settings
from app.schemas.confidence import DocumentConfidence, FieldConfidence
from app.schemas.extraction_base import ExtractionMeta, FieldStatus

# Baseline for fields with no dedicated reconciliation check below — not
# zero (an extracted value is still evidence) and not high enough to mask
# fields we haven't built specific checks for yet.
_DEFAULT_HEURISTIC = 0.6

# A confirmed disagreement between the two models on an escalated field is
# strong evidence the value is wrong — cap confidence regardless of what
# either model self-reported.
_DISAGREEMENT_CAP = 0.4


def _default_tracked_fields(extraction: BaseModel) -> list[str]:
    # Derived from the extraction's own (schema-specific) fields, minus the
    # ExtractionMeta fields every schema inherits — works for any
    # implemented document type, not just invoices.
    meta_fields = set(ExtractionMeta.model_fields)
    return [name for name in type(extraction).model_fields if name not in meta_fields]


def _values_match(a, b) -> bool:
    if a is None or b is None:
        return a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) < 0.01
    if isinstance(a, str) and isinstance(b, str):
        return a.strip().lower() == b.strip().lower()
    return a == b


def _line_items_reconcile(extraction: BaseModel) -> float:
    line_items = getattr(extraction, "line_items", None)
    subtotal = getattr(extraction, "subtotal", None)
    if not line_items or subtotal is None:
        return 0.5  # no cross-check possible either way
    total = sum(li.line_total or 0 for li in line_items)
    return 1.0 if abs(total - subtotal) < 0.01 else 0.3


def _heuristic_score(
    field_name: str, extraction: BaseModel, ocr_confidence: float | None = None
) -> float:
    value = getattr(extraction, field_name, None)
    if value in (None, "", []):
        return 0.0

    subtotal = getattr(extraction, "subtotal", None)
    tax_amount = getattr(extraction, "tax_amount", None)

    if field_name == "line_items":
        base = _line_items_reconcile(extraction)
    elif field_name == "total_amount" and subtotal is not None and tax_amount is not None:
        expected = subtotal + tax_amount
        base = 1.0 if abs(expected - value) < 0.01 else 0.3
    else:
        base = _DEFAULT_HEURISTIC

    # A field pulled from a poorly-OCR'd scan is less trustworthy than the
    # same value read off a clean digital page, even if it passed every
    # other check — fold OCR quality in as a multiplicative discount.
    ocr_factor = ocr_confidence if ocr_confidence is not None else 1.0
    return base * ocr_factor


def score_document(
    document_id: int,
    extraction: BaseModel,
    escalated: bool = False,
    prior_extraction: BaseModel | None = None,
    ocr_confidence: float | None = None,
) -> DocumentConfidence:
    """Score an extraction's per-field confidence.

    `prior_extraction` is the pre-escalation (DeepSeek) result — pass it
    when `escalated=True` to compute real cross-model agreement instead of
    leaving it unset. Disagreement caps confidence regardless of what
    either model self-reported, since two models landing on different
    values is stronger evidence of a wrong extraction than a single low
    self-reported score.

    `ocr_confidence` is the mean PaddleOCR confidence across the document's
    scanned pages (None for digital documents with no OCR involved) — folded
    into every field's heuristic score as a discount, since a value pulled
    from a poorly-OCR'd page is less trustworthy regardless of what the LLM
    or reconciliation checks say about it.
    """
    tracked_fields = list(extraction.field_status.keys()) or _default_tracked_fields(extraction)

    fields: list[FieldConfidence] = []
    for name in tracked_fields:
        status = extraction.field_status.get(name, FieldStatus.EXTRACTED)
        if status == FieldStatus.NOT_APPLICABLE:
            continue

        self_reported = extraction.self_reported_confidence.get(name, 0.5)
        heuristic = _heuristic_score(name, extraction, ocr_confidence)
        composite = 0.5 * self_reported + 0.5 * heuristic
        if status == FieldStatus.ILLEGIBLE:
            composite = min(composite, 0.3)

        cross_model_agreement = None
        if prior_extraction is not None and hasattr(prior_extraction, name):
            cross_model_agreement = _values_match(
                getattr(extraction, name), getattr(prior_extraction, name)
            )
            if cross_model_agreement is False:
                composite = min(composite, _DISAGREEMENT_CAP)

        fields.append(
            FieldConfidence(
                field_name=name,
                self_reported=self_reported,
                heuristic_score=heuristic,
                composite=composite,
                escalated=escalated,
                cross_model_agreement=cross_model_agreement,
            )
        )

    aggregate = sum(f.composite for f in fields) / len(fields) if fields else 0.0
    return DocumentConfidence(
        document_id=document_id,
        fields=fields,
        aggregate=aggregate,
        # Every document requires a human review step — confidence informs
        # escalation (see needs_escalation) and which fields get flagged for
        # extra scrutiny during review, but never skips review outright.
        needs_review=True,
    )


def needs_escalation(confidence: DocumentConfidence) -> bool:
    return confidence.aggregate < settings.confidence_escalation_threshold
