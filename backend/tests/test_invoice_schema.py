import pytest
from pydantic import ValidationError

from app.schemas.invoice import FieldStatus, InvoiceExtraction, LineItem


def test_valid_extraction_with_nested_line_items():
    extraction = InvoiceExtraction(
        invoice_number="INV-1001",
        invoice_date="2026-07-01",
        vendor_name="Acme Supplies",
        subtotal=100.0,
        tax_amount=8.0,
        total_amount=108.0,
        line_items=[
            LineItem(description="Widget", quantity=2, unit_price=50.0, line_total=100.0),
        ],
        field_status={"po_number": FieldStatus.NOT_APPLICABLE},
        self_reported_confidence={"invoice_number": 0.95, "vendor_name": 0.9},
    )
    assert extraction.po_number is None
    assert extraction.field_status["po_number"] == FieldStatus.NOT_APPLICABLE
    assert extraction.line_items[0].line_total == 100.0


def test_missing_fields_default_to_none_not_error():
    extraction = InvoiceExtraction()
    assert extraction.invoice_number is None
    assert extraction.line_items == []


def test_invalid_date_raises_validation_error():
    with pytest.raises(ValidationError):
        InvoiceExtraction(invoice_date="not-a-date")
