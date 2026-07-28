"""Shared across every document type's extraction schema (invoice, resume,
...). Each concrete schema (InvoiceExtraction, ResumeExtraction) inherits
from ExtractionMeta alongside its own fields, so confidence.py can find
"which fields carry status/confidence metadata vs. real extracted data"
generically instead of hardcoding one schema's field names.
"""

from enum import Enum

from pydantic import BaseModel, Field


class FieldStatus(str, Enum):
    """Distinguishes "couldn't extract" from "doesn't exist on this document".

    A null value alone is ambiguous — did the model fail to find a due date,
    or does this invoice simply not have payment terms? Collapsing both into
    None would corrupt confidence scoring (a genuinely absent field should
    not be penalized as a low-confidence extraction) and the accuracy report
    (ground truth needs the same three-way distinction to score fairly).
    """

    EXTRACTED = "extracted"
    NOT_APPLICABLE = "not_applicable"
    ILLEGIBLE = "illegible"


class ExtractionMeta(BaseModel):
    field_status: dict[str, FieldStatus] = Field(
        default_factory=dict,
        description="Per top-level field name, whether it was extracted, "
        "is not applicable to this document, or was present but illegible.",
    )
    self_reported_confidence: dict[str, float] = Field(
        default_factory=dict,
        description="Per top-level field name, the model's own 0-1 "
        "confidence in the extracted value. Only meaningful for fields "
        "with status EXTRACTED; combined downstream with heuristic checks "
        "into a composite score — never used alone as the final confidence.",
    )
