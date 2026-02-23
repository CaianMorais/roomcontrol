"""add is_deleted to rooms

Revision ID: 41cc95317f1a
Revises: ada6abda7da2
Create Date: 2026-02-23 14:39:25.959973

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '41cc95317f1a'
down_revision: Union[str, Sequence[str], None] = 'ada6abda7da2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("rooms", sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    op.drop_column('rooms', 'is_deleted')
