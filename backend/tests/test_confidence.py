from app.schemas.invoice import FieldStatus, InvoiceExtraction, LineItem
from app.services import confidence as confidence_service


def test_not_applicable_fields_excluded_from_scoring():
    extraction = InvoiceExtraction(
        invoice_number="INV-1",
        field_status={"po_number": FieldStatus.NOT_APPLICABLE},
        self_reported_confidence={"invoice_number": 0.9},
    )
    result = confidence_service.score_document(1, extraction)
    assert "po_number" not in [f.field_name for f in result.fields]


def test_line_item_reconciliation_lowers_heuristic_on_mismatch():
    extraction = InvoiceExtraction(
        subtotal=100.0,
        line_items=[LineItem(description="Widget", line_total=50.0)],
        field_status={"line_items": FieldStatus.EXTRACTED},
        self_reported_confidence={"line_items": 0.9},
    )
    result = confidence_service.score_document(1, extraction)
    line_items_conf = next(f for f in result.fields if f.field_name == "line_items")
    assert line_items_conf.heuristic_score < 0.5


def test_illegible_field_caps_composite_low():
    extraction = InvoiceExtraction(
        invoice_number="???",
        field_status={"invoice_number": FieldStatus.ILLEGIBLE},
        self_reported_confidence={"invoice_number": 0.9},
    )
    result = confidence_service.score_document(1, extraction)
    field = next(f for f in result.fields if f.field_name == "invoice_number")
    assert field.composite <= 0.3


def test_needs_escalation_below_threshold():
    extraction = InvoiceExtraction(
        invoice_number=None,
        field_status={"invoice_number": FieldStatus.EXTRACTED},
        self_reported_confidence={"invoice_number": 0.1},
    )
    result = confidence_service.score_document(1, extraction)
    assert confidence_service.needs_escalation(result)


def test_fallback_tracked_fields_excludes_meta_fields_and_includes_line_items():
    # No field_status set at all — this is the fallback branch that used to
    # score "field_status" and "self_reported_confidence" as if they were
    # real invoice fields, and skip line_items entirely.
    extraction = InvoiceExtraction(
        invoice_number="INV-1",
        subtotal=100.0,
        line_items=[LineItem(description="Widget", line_total=100.0)],
    )
    result = confidence_service.score_document(1, extraction)
    names = [f.field_name for f in result.fields]
    assert "field_status" not in names
    assert "self_reported_confidence" not in names
    assert "line_items" in names


def test_cross_model_agreement_detected_on_match():
    prior = InvoiceExtraction(vendor_name="Acme Supply Co.")
    escalated = InvoiceExtraction(
        vendor_name="Acme Supply Co.",
        field_status={"vendor_name": FieldStatus.EXTRACTED},
        self_reported_confidence={"vendor_name": 0.9},
    )
    result = confidence_service.score_document(
        1, escalated, escalated=True, prior_extraction=prior
    )
    field = next(f for f in result.fields if f.field_name == "vendor_name")
    assert field.cross_model_agreement is True


def test_cross_model_disagreement_caps_composite():
    prior = InvoiceExtraction(vendor_name="Acme Supply Co.")
    escalated = InvoiceExtraction(
        vendor_name="Northgate Manufacturing",
        field_status={"vendor_name": FieldStatus.EXTRACTED},
        self_reported_confidence={"vendor_name": 0.95},
    )
    result = confidence_service.score_document(
        1, escalated, escalated=True, prior_extraction=prior
    )
    field = next(f for f in result.fields if f.field_name == "vendor_name")
    assert field.cross_model_agreement is False
    assert field.composite <= confidence_service._DISAGREEMENT_CAP


def test_ocr_confidence_discounts_heuristic_score():
    extraction = InvoiceExtraction(
        vendor_name="Acme Supply Co.",
        field_status={"vendor_name": FieldStatus.EXTRACTED},
        self_reported_confidence={"vendor_name": 0.9},
    )
    clean = confidence_service.score_document(1, extraction, ocr_confidence=1.0)
    poor_scan = confidence_service.score_document(1, extraction, ocr_confidence=0.3)

    clean_field = next(f for f in clean.fields if f.field_name == "vendor_name")
    poor_field = next(f for f in poor_scan.fields if f.field_name == "vendor_name")
    assert poor_field.heuristic_score < clean_field.heuristic_score
    assert poor_field.composite < clean_field.composite


def test_ocr_confidence_none_leaves_heuristic_unchanged():
    extraction = InvoiceExtraction(
        vendor_name="Acme Supply Co.",
        field_status={"vendor_name": FieldStatus.EXTRACTED},
        self_reported_confidence={"vendor_name": 0.9},
    )
    no_ocr = confidence_service.score_document(1, extraction)
    explicit_full = confidence_service.score_document(1, extraction, ocr_confidence=1.0)
    assert no_ocr.fields[0].heuristic_score == explicit_full.fields[0].heuristic_score
