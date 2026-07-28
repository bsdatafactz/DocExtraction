"""add projects table and document project_id

Revision ID: 39a39f45120f
Revises: e0612b5a427a
Create Date: 2026-07-27 14:58:59.256857

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '39a39f45120f'
down_revision: Union[str, None] = 'e0612b5a427a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=256), nullable=False),
        sa.Column('document_type', sa.String(length=32), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    # documents.project_id can't be added NOT NULL directly if rows already
    # exist — add nullable, backfill onto a default project, then tighten.
    op.add_column('documents', sa.Column('project_id', sa.Integer(), nullable=True))

    connection = op.get_bind()
    connection.execute(
        sa.text(
            "INSERT INTO projects (name, document_type, created_at) "
            "VALUES ('Invoices', 'invoice', now())"
        )
    )
    default_project_id = connection.execute(
        sa.text("SELECT id FROM projects WHERE name = 'Invoices' ORDER BY id DESC LIMIT 1")
    ).scalar_one()
    connection.execute(
        sa.text("UPDATE documents SET project_id = :pid WHERE project_id IS NULL"),
        {"pid": default_project_id},
    )

    op.alter_column('documents', 'project_id', nullable=False)
    op.create_foreign_key(
        'fk_documents_project_id', 'documents', 'projects', ['project_id'], ['id']
    )


def downgrade() -> None:
    op.drop_constraint('fk_documents_project_id', 'documents', type_='foreignkey')
    op.drop_column('documents', 'project_id')
    op.drop_table('projects')
