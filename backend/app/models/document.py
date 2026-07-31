"""Audit-trail data model.

Deliberately not a single "final record" table: raw per-model extractions,
per-field confidence, and human corrections are kept as separate history so
the accuracy report can compare raw-extraction accuracy against post-review
accuracy on the same ground-truth set. See CLAUDE.md.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.project import Project


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    filename: Mapped[str] = mapped_column(String(512))
    file_path: Mapped[str] = mapped_column(String(1024))
    status: Mapped[str] = mapped_column(String(32), default="queued")
    is_scanned: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Real measurements for the dashboard, not estimates — set by
    # pipeline.py at each stage boundary.
    parsing_started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    parsing_completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    extraction_started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    extraction_completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="documents")
    extractions: Mapped[list["Extraction"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
    field_confidences: Mapped[list["FieldConfidenceRecord"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
    corrections: Mapped[list["Correction"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class Extraction(Base):
    """One row per model call — DeepSeek's first pass, and the Azure OpenAI escalation model's if escalated."""

    __tablename__ = "extractions"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    model_name: Mapped[str] = mapped_column(String(64))
    raw_json: Mapped[dict] = mapped_column(JSON)
    is_escalation: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    # Nullable: rows written before token capture existed have no usage data
    # and are excluded from cost totals rather than costed as zero-token
    # calls (see services/cost.py).
    prompt_tokens: Mapped[int | None] = mapped_column(nullable=True)
    completion_tokens: Mapped[int | None] = mapped_column(nullable=True)

    document: Mapped["Document"] = relationship(back_populates="extractions")


class FieldConfidenceRecord(Base):
    __tablename__ = "field_confidences"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    field_name: Mapped[str] = mapped_column(String(128))
    self_reported: Mapped[float] = mapped_column(Float)
    heuristic_score: Mapped[float] = mapped_column(Float)
    composite: Mapped[float] = mapped_column(Float)
    escalated: Mapped[bool] = mapped_column(Boolean, default=False)
    cross_model_agreement: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    document: Mapped["Document"] = relationship(back_populates="field_confidences")


class Correction(Base):
    """Human review edits — kept distinct from the raw model extraction."""

    __tablename__ = "corrections"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    field_name: Mapped[str] = mapped_column(String(128))
    # Text, not String — a corrected line_items value is a JSON-encoded list
    # and can exceed a fixed-length column for invoices with many items.
    corrected_value: Mapped[str] = mapped_column(Text, nullable=True)
    reviewer: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    document: Mapped["Document"] = relationship(back_populates="corrections")
