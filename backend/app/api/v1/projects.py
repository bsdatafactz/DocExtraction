import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.ownership import can_access_project, owned_projects_query
from app.db.session import get_db
from app.models.project import Project
from app.models.user import User
from app.schemas.project import IMPLEMENTED_DOCUMENT_TYPES, ProjectCreate, ProjectSummary

router = APIRouter(prefix="/projects", tags=["projects"])


def _to_summary(project: Project) -> ProjectSummary:
    summary = ProjectSummary.model_validate(project)
    summary.is_implemented = project.document_type in IMPLEMENTED_DOCUMENT_TYPES
    return summary


@router.post("", response_model=ProjectSummary)
def create_project(
    request: ProjectCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProjectSummary:
    project = Project(
        name=request.name, document_type=request.document_type.value, owner_id=user.id
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return _to_summary(project)


@router.get("", response_model=list[ProjectSummary])
def list_projects(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> list[ProjectSummary]:
    projects = owned_projects_query(db, user).order_by(Project.created_at.desc()).all()
    return [_to_summary(p) for p in projects]


@router.get("/{project_id}", response_model=ProjectSummary)
def get_project(
    project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> ProjectSummary:
    project = db.get(Project, project_id)
    if project is None or not can_access_project(project, user):
        raise HTTPException(status_code=404, detail="Project not found")
    return _to_summary(project)


@router.delete("/{project_id}", status_code=204)
def delete_project(
    project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> None:
    project = db.get(Project, project_id)
    if project is None or not can_access_project(project, user):
        raise HTTPException(status_code=404, detail="Project not found")

    for document in project.documents:
        if os.path.exists(document.file_path):
            os.remove(document.file_path)

    db.delete(project)
    db.commit()
