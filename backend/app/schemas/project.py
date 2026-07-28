from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict

# Matches the brief's own four allowed document types. Only INVOICE has a
# real extraction schema/pipeline (see app/schemas/invoice.py) — the others
# are genuine, selectable values, not placeholders, but a project created
# with one of them can't have documents extracted yet.
IMPLEMENTED_DOCUMENT_TYPES = {"invoice"}


class DocumentType(str, Enum):
    INVOICE = "invoice"
    RESUME = "resume"
    PURCHASE_ORDER = "purchase_order"
    CONTRACT = "contract"


class ProjectCreate(BaseModel):
    name: str
    document_type: DocumentType


class ProjectSummary(BaseModel):
    id: int
    name: str
    document_type: DocumentType
    created_at: datetime
    is_implemented: bool = True

    model_config = ConfigDict(from_attributes=True)
