"""add project owner_id

Revision ID: a1b2c3d4e5f6
Revises: 7a3d7d13fc74
Create Date: 2026-07-28 17:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '7a3d7d13fc74'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Nullable, not backfilled: projects created before ownership existed
    # have no owner and become admin-only visible rather than being
    # assigned to an arbitrary user.
    op.add_column('projects', sa.Column('owner_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_projects_owner_id', 'projects', 'users', ['owner_id'], ['id']
    )


def downgrade() -> None:
    op.drop_constraint('fk_projects_owner_id', 'projects', type_='foreignkey')
    op.drop_column('projects', 'owner_id')
