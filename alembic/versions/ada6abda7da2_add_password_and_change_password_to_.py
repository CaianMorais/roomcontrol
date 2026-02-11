"""add_password_and_change_password_to_collaborators

Revision ID: ada6abda7da2
Revises: 7a29e068ec4d
Create Date: 2026-02-11 15:34:15.957025

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ada6abda7da2'
down_revision: Union[str, Sequence[str], None] = '7a29e068ec4d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'collaborators',
        sa.Column('password', sa.String(length=255), nullable=False)
    )

    op.add_column(
        'collaborators',
        sa.Column('change_password', sa.Boolean(), nullable=False, server_default='1')
    )


def downgrade() -> None:
    op.drop_column('collaborators', 'change_password')
    op.drop_column('collaborators', 'password_hash')
