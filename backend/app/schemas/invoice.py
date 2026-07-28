"""LLM-facing extraction contract for invoices.

This is the schema handed to the LLM as its structured-output target, and
what extraction results are validated against before anything is persisted.
"""

from datetime import date
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


class LineItem(BaseModel):
    description: str
    quantity: float | None = None
    unit_price: float | None = None
    line_total: float | None = None


class InvoiceExtraction(BaseModel):
    invoice_number: str | None = None
    invoice_date: date | None = None
    due_date: date | None = None
    po_number: str | None = None
    vendor_name: str | None = None
    vendor_address: str | None = None
    vendor_tax_id: str | None = None
    customer_name: str | None = None
    customer_address: str | None = None
    currency: str | None = None
    subtotal: float | None = None
    tax_amount: float | None = None
    total_amount: float | None = None
    payment_terms: str | None = None
    line_items: list[LineItem] = Field(default_factory=list)

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
