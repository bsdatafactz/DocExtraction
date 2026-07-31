from pydantic import BaseModel


class ProjectCost(BaseModel):
    project_id: int
    project_name: str
    document_count: int
    total_cost: float


class UserCost(BaseModel):
    user_id: int | None
    email: str
    project_count: int
    total_cost: float


class CostSummary(BaseModel):
    overall_total_cost: float
    projects: list[ProjectCost]
    # Admin only — per-owner breakdown across every user's projects,
    # including a "(orphaned projects)" row for owner_id IS NULL.
    users: list[UserCost] | None = None
