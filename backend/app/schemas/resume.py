"""LLM-facing extraction contract for resumes — the second real document
type, alongside invoices. Same pattern: a fixed schema every resume gets
extracted into, not something that varies per document.
"""

from pydantic import BaseModel, Field

from app.schemas.extraction_base import ExtractionMeta

__all__ = ["WorkExperience", "ResumeProject", "Education", "ResumeExtraction"]


class WorkExperience(BaseModel):
    company: str
    title: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    description: str | None = None


class ResumeProject(BaseModel):
    name: str
    description: str | None = None
    technologies: str | None = None


class Education(BaseModel):
    institution: str
    degree: str | None = None
    field_of_study: str | None = None
    graduation_year: str | None = None


class ResumeExtraction(ExtractionMeta):
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    professional_summary: str | None = None
    skills: list[str] = Field(default_factory=list)
    work_experience: list[WorkExperience] = Field(default_factory=list)
    projects: list[ResumeProject] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
