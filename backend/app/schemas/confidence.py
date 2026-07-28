"""Composite confidence — never a single raw model-reported number.

Per-field score = self_reported (from the LLM) combined with heuristic_score
(format/regex validity, OCR-region confidence, line-item-sum-vs-total
reconciliation). See CLAUDE.md for the escalation rule this feeds into.
"""

from pydantic import BaseModel, Field


class FieldConfidence(BaseModel):
    field_name: str
    self_reported: float = Field(ge=0, le=1)
    heuristic_score: float = Field(ge=0, le=1)
    composite: float = Field(ge=0, le=1)
    escalated: bool = False
    cross_model_agreement: bool | None = None


class DocumentConfidence(BaseModel):
    document_id: int
    fields: list[FieldConfidence]
    aggregate: float = Field(ge=0, le=1)
    needs_review: bool
