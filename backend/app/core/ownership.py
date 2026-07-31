"""Project ownership scoping.

Every user — including admin — only ever sees their own projects and
documents. Admin is a role for user management and testing, not
cross-tenant visibility: each user reviews their own documents, and admin
never needs to see or review anyone else's. The one exception is projects
orphaned by a deleted owner (owner_id is NULL) — those stay admin-visible
since no user can claim them, rather than becoming permanently
inaccessible through the UI.
"""

from sqlalchemy import or_
from sqlalchemy.orm import Query, Session
from sqlalchemy.sql.elements import ColumnElement

from app.models.project import Project
from app.models.user import User


def owner_condition(user: User) -> ColumnElement[bool]:
    if user.role == "admin":
        return or_(Project.owner_id == user.id, Project.owner_id.is_(None))
    return Project.owner_id == user.id


def owned_projects_query(db: Session, user: User) -> Query:
    return db.query(Project).filter(owner_condition(user))


def can_access_project(project: Project, user: User) -> bool:
    if project.owner_id == user.id:
        return True
    return user.role == "admin" and project.owner_id is None
