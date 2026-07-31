"""add extraction token usage

Revision ID: 7558a54364e6
Revises: a1b2c3d4e5f6
Create Date: 2026-07-30 17:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7558a54364e6'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('extractions', sa.Column('prompt_tokens', sa.Integer(), nullable=True))
    op.add_column('extractions', sa.Column('completion_tokens', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('extractions', 'completion_tokens')
    op.drop_column('extractions', 'prompt_tokens')
