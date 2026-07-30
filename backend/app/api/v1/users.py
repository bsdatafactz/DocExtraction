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

    # Orphan rather than cascade-delete their projects — same "no owner ==
    # admin-only visibility" state Project already supports for projects
    # created before ownership existed (see app/models/project.py). Deleting
    # a user should never silently destroy their documents/extractions.
    db.query(Project).filter(Project.owner_id == user_id).update({"owner_id": None})
    db.delete(user)
    db.commit()
