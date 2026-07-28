"""LLM-facing extraction contract for invoices.

This is the schema handed to the LLM as its structured-output target, and
what extraction results are validated against before anything is persisted.
"""

from datetime import date

from pydantic import BaseModel, Field

from app.schemas.extraction_base import ExtractionMeta, FieldStatus

__all__ = ["FieldStatus", "LineItem", "InvoiceExtraction"]


class LineItem(BaseModel):
    description: str
    quantity: float | None = None
    unit_price: float | None = None
    line_total: float | None = None


class InvoiceExtraction(ExtractionMeta):
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
