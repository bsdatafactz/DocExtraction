"""Seed a few documents directly into the DB, bypassing real LLM calls.

For UI development/testing before API keys are configured — populates the
queue and a needs_review document with realistic extraction + confidence
data so the review screen has something real to render.
"""

import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.document import Document, Extraction, FieldConfidenceRecord
from app.models.project import Project

TEST_SET = Path(__file__).resolve().parents[2] / "test_set"


def _copy_sample(src: Path, dest_name: str) -> str:
    os.makedirs(settings.upload_dir, exist_ok=True)
    dest = os.path.join(settings.upload_dir, dest_name)
    shutil.copy(src, dest)
    return dest


def seed():
    db = SessionLocal()

    project = db.query(Project).filter(Project.document_type == "invoice").first()
    if project is None:
        project = Project(name="Invoices", document_type="invoice")
        db.add(project)
        db.flush()

    # 1. A needs_review document with realistic mixed confidence — the one
    #    the review screen actually gets tested against.
    file_path = _copy_sample(TEST_SET / "scanned" / "scanned_02.pdf", "demo_needs_review.pdf")
    doc = Document(
        project_id=project.id,
        filename="acme_supply_invoice_0417.pdf",
        file_path=file_path,
        status="needs_review",
        is_scanned=True,
    )
    db.add(doc)
    db.flush()

    extraction = {
        "invoice_number": "INV-70142",
        "invoice_date": "2026-03-14",
        "due_date": None,
        "po_number": None,
        "vendor_name": "Acme Supply Co.",
        "vendor_address": "48 Foundry Rd, Springfield",
        "vendor_tax_id": None,
        "customer_name": "Northgate Manufacturing",
        "customer_address": None,
        "currency": "USD",
        "subtotal": 1239.50,
        "tax_amount": 45.00,
        "total_amount": 1284.50,
        "payment_terms": "Net 30",
        "line_items": [
            {"description": "Steel brackets", "quantity": 40, "unit_price": 18.50, "line_total": 740.00},
            {"description": "Shipping", "quantity": 1, "unit_price": 45.00, "line_total": 45.00},
        ],
        "field_status": {"due_date": "not_applicable", "po_number": "not_applicable"},
        "self_reported_confidence": {
            "invoice_number": 0.9,
            "invoice_date": 0.3,
            "vendor_name": 0.95,
            "total_amount": 0.88,
        },
    }
    db.add(Extraction(document_id=doc.id, model_name="deepseek-chat", raw_json=extraction))

    field_confidences = [
        ("invoice_number", 0.9, 0.8, 0.85),
        ("invoice_date", 0.3, 0.4, 0.35),  # low — OCR skew made the date ambiguous
        ("vendor_name", 0.95, 0.9, 0.92),
        ("total_amount", 0.88, 1.0, 0.94),  # reconciles against subtotal+tax
        ("line_items", 0.8, 0.6, 0.7),
    ]
    for name, self_reported, heuristic, composite in field_confidences:
        db.add(
            FieldConfidenceRecord(
                document_id=doc.id,
                field_name=name,
                self_reported=self_reported,
                heuristic_score=heuristic,
                composite=composite,
            )
        )

    # 2. A couple more documents so the queue view isn't a single row.
    for name, status in [
        ("beacon_traders_march.pdf", "approved"),
        ("harborline_freight_02.pdf", "queued"),
        ("crestview_parts_invoice.pdf", "extracting"),
    ]:
        fp = _copy_sample(TEST_SET / "digital" / "digital_01.pdf", f"demo_{status}.pdf")
        db.add(
            Document(
                project_id=project.id, filename=name, file_path=fp, status=status, is_scanned=False
            )
        )

    db.commit()
    print(f"Seeded needs_review document id={doc.id} plus 3 queue filler documents")


if __name__ == "__main__":
    seed()
