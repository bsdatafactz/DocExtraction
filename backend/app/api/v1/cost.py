from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.ownership import owned_projects_query
from app.db.session import get_db
from app.models.document import Document, Extraction
from app.models.project import Project
from app.models.user import User
from app.schemas.cost import CostSummary, ProjectCost, UserCost
from app.services.cost import extraction_cost

router = APIRouter(prefix="/cost", tags=["cost"])


def _cost_by_project(db: Session) -> dict[int, float]:
    rows = (
        db.query(
            Document.project_id,
            Extraction.is_escalation,
            Extraction.prompt_tokens,
            Extraction.completion_tokens,
        )
        .join(Extraction, Extraction.document_id == Document.id)
        .all()
    )
    totals: dict[int, float] = {}
    for project_id, is_escalation, prompt_tokens, completion_tokens in rows:
        totals[project_id] = totals.get(project_id, 0.0) + extraction_cost(
            is_escalation, prompt_tokens, completion_tokens
        )
    return totals


@router.get("", response_model=CostSummary)
def get_cost_summary(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> CostSummary:
    cost_by_project = _cost_by_project(db)

    # Same visibility rule as everywhere else: a regular user sees only
    # their own projects; admin sees their own + orphaned ones here too,
    # with the full cross-user picture added below.
    own_projects = owned_projects_query(db, user).all()
    project_costs = [
        ProjectCost(
            project_id=p.id,
            project_name=p.name,
            document_count=len(p.documents),
            total_cost=round(cost_by_project.get(p.id, 0.0), 4),
        )
        for p in own_projects
    ]

    users_breakdown = None
    overall_total = sum(pc.total_cost for pc in project_costs)

    if user.role == "admin":
        all_projects = db.query(Project).all()
        cost_by_owner: dict[int | None, float] = {}
        count_by_owner: dict[int | None, int] = {}
        for p in all_projects:
            project_total = cost_by_project.get(p.id, 0.0)
            cost_by_owner[p.owner_id] = cost_by_owner.get(p.owner_id, 0.0) + project_total
            count_by_owner[p.owner_id] = count_by_owner.get(p.owner_id, 0) + 1

        users_by_id = {u.id: u for u in db.query(User).all()}
        users_breakdown = [
            UserCost(
                user_id=owner_id,
                email=users_by_id[owner_id].email if owner_id in users_by_id else "(orphaned projects)",
                project_count=count_by_owner[owner_id],
                total_cost=round(cost, 4),
            )
            for owner_id, cost in sorted(cost_by_owner.items(), key=lambda kv: kv[1], reverse=True)
        ]
        overall_total = sum(cost_by_project.values())

    return CostSummary(
        overall_total_cost=round(overall_total, 4),
        projects=project_costs,
        users=users_breakdown,
    )
