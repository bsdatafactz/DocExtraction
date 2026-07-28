"""API request/response models for the document upload & queue endpoints."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict

from app.schemas.confidence import DocumentConfidence
from app.schemas.invoice import InvoiceExtraction


class DocumentStatus(str, Enum):
    QUEUED = "queued"
    PARSING = "parsing"
    EXTRACTING = "extracting"
    ESCALATED = "escalated"
    NEEDS_REVIEW = "needs_review"
    APPROVED = "approved"
    FAILED = "failed"


class DocumentSummary(BaseModel):
    id: int
    filename: str
    status: DocumentStatus
    created_at: datetime
    aggregate_confidence: float | None = None

    model_config = ConfigDict(from_attributes=True)


class DocumentDetail(DocumentSummary):
    extraction: InvoiceExtraction | None = None
    confidence: DocumentConfidence | None = None


class UploadResponse(BaseModel):
    id: int
    filename: str
    status: DocumentStatus


class CorrectionRequest(BaseModel):
    corrected_fields: dict[str, str | float | None | list[dict]]
    # False = "flag for follow-up": persist the edits but leave the document
    # in needs_review rather than marking it approved.
    approve: bool = True
