from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_projects: int
    total_documents: int
    status_counts: dict[str, int]
    avg_parsing_seconds: float | None
    avg_extraction_seconds: float | None
    scanned_count: int
    error_count: int
    error_rate: float
    escalation_count: int
    escalation_rate: float
    auto_approved_count: int
    reviewed_count: int
