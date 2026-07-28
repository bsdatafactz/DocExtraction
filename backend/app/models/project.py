"""A project scopes a batch of documents to one document type.

Only "invoice" has an actual extraction pipeline wired up (schema, prompts,
confidence heuristics — see app/schemas/invoice.py and app/services/). Other
document types are real, selectable enum values — not placeholders — but
uploading to one currently returns a 400 rather than silently running the
invoice pipeline against the wrong schema.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(256))
    document_type: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    # Nullable: projects created before ownership existed have no owner and
    # are only visible to admins (see list/get scoping in api/v1/projects.py)
    # rather than being backfilled onto an arbitrary user.
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    documents: Mapped[list["Document"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
