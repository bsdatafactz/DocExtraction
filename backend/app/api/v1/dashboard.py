from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Query, Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.document import Correction, Document, Extraction
from app.models.project import Project
from app.models.user import User
from app.schemas.dashboard import DailyCount, DashboardStats

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

_TREND_DAYS = 30


def _scoped_documents(db: Session, user: User) -> Query:
    # Admins see every user's documents; everyone else only sees documents
    # in projects they own — same rule as the projects/documents list
    # endpoints, so the dashboard never shows a regular user numbers that
    # include someone else's uploads.
    query = db.query(Document)
    if user.role != "admin":
        query = query.join(Project, Document.project_id == Project.id).filter(
            Project.owner_id == user.id
        )
    return query


def _avg_seconds(db: Session, user: User, start_col, end_col) -> float | None:
    seconds_expr = func.extract("epoch", end_col - start_col)
    result = (
        _scoped_documents(db, user)
        .filter(start_col.isnot(None), end_col.isnot(None))
        .with_entities(func.avg(seconds_expr))
        .scalar()
    )
    return round(float(result), 2) if result is not None else None


def _daily_uploads(db: Session, user: User) -> list[DailyCount]:
    since = datetime.utcnow() - timedelta(days=_TREND_DAYS - 1)
    day = func.date(Document.created_at)
    rows = (
        _scoped_documents(db, user)
        .filter(Document.created_at >= since)
        .with_entities(day.label("day"), func.count(Document.id))
        .group_by(day)
        .all()
    )
    counts_by_day = {str(d): c for d, c in rows}

    result = []
    for i in range(_TREND_DAYS):
        d = (since + timedelta(days=i)).date()
        result.append(DailyCount(date=str(d), count=counts_by_day.get(str(d), 0)))
    return result


@router.get("", response_model=DashboardStats)
def get_dashboard(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> DashboardStats:
    is_admin = user.role == "admin"

    total_users = (db.query(func.count(User.id)).scalar() or 0) if is_admin else 0

    project_query = db.query(Project)
    if not is_admin:
        project_query = project_query.filter(Project.owner_id == user.id)
    total_projects = project_query.count()

    total_documents = _scoped_documents(db, user).count()

    status_rows = (
        _scoped_documents(db, user)
        .with_entities(Document.status, func.count(Document.id))
        .group_by(Document.status)
        .all()
    )
    status_counts = {status: count for status, count in status_rows}

    error_count = status_counts.get("failed", 0)
    scanned_count = _scoped_documents(db, user).filter(Document.is_scanned.is_(True)).count()

    escalation_query = db.query(func.count(func.distinct(Extraction.document_id))).join(
        Document, Extraction.document_id == Document.id
    )
    if not is_admin:
        escalation_query = escalation_query.join(
            Project, Document.project_id == Project.id
        ).filter(Project.owner_id == user.id)
    escalation_count = escalation_query.filter(Extraction.is_escalation.is_(True)).scalar() or 0

    reviewed_query = db.query(func.count(func.distinct(Correction.document_id))).join(
        Document, Correction.document_id == Document.id
    )
    if not is_admin:
        reviewed_query = reviewed_query.join(
            Project, Document.project_id == Project.id
        ).filter(Project.owner_id == user.id)
    reviewed_count = reviewed_query.scalar() or 0

    auto_approved_count = (
        _scoped_documents(db, user)
        .filter(Document.status == "approved")
        .filter(~Document.id.in_(db.query(Correction.document_id).distinct()))
        .count()
    )

    return DashboardStats(
        total_users=total_users,
        total_projects=total_projects,
        total_documents=total_documents,
        status_counts=status_counts,
        avg_parsing_seconds=_avg_seconds(
            db, user, Document.parsing_started_at, Document.parsing_completed_at
        ),
        avg_extraction_seconds=_avg_seconds(
            db, user, Document.extraction_started_at, Document.extraction_completed_at
        ),
        avg_processing_seconds=_avg_seconds(
            db, user, Document.parsing_started_at, Document.extraction_completed_at
        ),
        scanned_count=scanned_count,
        error_count=error_count,
        error_rate=round(error_count / total_documents, 3) if total_documents else 0.0,
        escalation_count=escalation_count,
        escalation_rate=round(escalation_count / total_documents, 3) if total_documents else 0.0,
        auto_approved_count=auto_approved_count,
        reviewed_count=reviewed_count,
        daily_uploads=_daily_uploads(db, user),
    )
