import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import require_admin
from app.db.session import get_db
from app.models.project import Project
from app.models.user import User
from app.schemas.auth import RoleUpdateRequest, UserSummary

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserSummary])
def list_users(
    db: Session = Depends(get_db), _admin: User = Depends(require_admin)
) -> list[UserSummary]:
    users = db.query(User).order_by(User.created_at.asc()).all()
    return [UserSummary.model_validate(u) for u in users]


@router.patch("/{user_id}/role", response_model=UserSummary)
def update_role(
    user_id: int,
    request: RoleUpdateRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> UserSummary:
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="You can't change your own role")

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    user.role = request.role.value
    db.commit()
    db.refresh(user)
    return UserSummary.model_validate(user)


@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)
) -> None:
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="You can't delete your own account")

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    for project in db.query(Project).filter(Project.owner_id == user_id):
        for document in project.documents:
            if os.path.exists(document.file_path):
                os.remove(document.file_path)
        db.delete(project)

    # No relationship() links User <-> Project (owner_id is a plain FK
    # column), so the ORM has no dependency info to order these deletes —
    # flush the project deletes before deleting the user, or the FK
    # constraint can fire depending on flush ordering.
    db.flush()

    db.delete(user)
    db.commit()
