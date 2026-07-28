from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.document import Correction, Document, Extraction
from app.models.project import Project
from app.models.user import User
from app.schemas.dashboard import DashboardStats

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _avg_seconds(db: Session, start_col, end_col) -> float | None:
    seconds_expr = func.extract("epoch", end_col - start_col)
    result = db.query(func.avg(seconds_expr)).filter(
        start_col.isnot(None), end_col.isnot(None)
    ).scalar()
    return round(float(result), 2) if result is not None else None


@router.get("", response_model=DashboardStats)
def get_dashboard(
    db: Session = Depends(get_db), _user: User = Depends(get_current_user)
) -> DashboardStats:
    total_projects = db.query(func.count(Project.id)).scalar() or 0
    total_documents = db.query(func.count(Document.id)).scalar() or 0

    status_rows = db.query(Document.status, func.count(Document.id)).group_by(Document.status).all()
    status_counts = {status: count for status, count in status_rows}

    error_count = status_counts.get("failed", 0)
    scanned_count = db.query(func.count(Document.id)).filter(Document.is_scanned.is_(True)).scalar() or 0

    escalation_count = (
        db.query(func.count(func.distinct(Extraction.document_id)))
        .filter(Extraction.is_escalation.is_(True))
        .scalar()
        or 0
    )

    reviewed_count = (
        db.query(func.count(func.distinct(Correction.document_id))).scalar() or 0
    )
    auto_approved_count = (
        db.query(func.count(Document.id))
        .filter(Document.status == "approved")
        .filter(~Document.id.in_(db.query(Correction.document_id).distinct()))
        .scalar()
        or 0
    )

    return DashboardStats(
        total_projects=total_projects,
        total_documents=total_documents,
        status_counts=status_counts,
        avg_parsing_seconds=_avg_seconds(
            db, Document.parsing_started_at, Document.parsing_completed_at
        ),
        avg_extraction_seconds=_avg_seconds(
            db, Document.extraction_started_at, Document.extraction_completed_at
        ),
        scanned_count=scanned_count,
        error_count=error_count,
        error_rate=round(error_count / total_documents, 3) if total_documents else 0.0,
        escalation_count=escalation_count,
        escalation_rate=round(escalation_count / total_documents, 3) if total_documents else 0.0,
        auto_approved_count=auto_approved_count,
        reviewed_count=reviewed_count,
    )
