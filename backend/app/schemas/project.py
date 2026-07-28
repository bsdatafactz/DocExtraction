from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict

# Invoice and resume have real extraction schemas/pipelines (see
# app/schemas/invoice.py and app/schemas/resume.py). Contract is a genuine,
# selectable value, not a placeholder, but a project created with it can't
# have documents extracted yet — no fields have been specified for it.
IMPLEMENTED_DOCUMENT_TYPES = {"invoice", "resume"}


class DocumentType(str, Enum):
    INVOICE = "invoice"
    RESUME = "resume"
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
