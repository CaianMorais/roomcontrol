"""add is_deleted to guests

Revision ID: a45c632f01eb
Revises: aed301c57ca8
Create Date: 2025-09-29 09:33:40.742404

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = 'a45c632f01eb'
down_revision: Union[str, Sequence[str], None] = 'aed301c57ca8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('guests', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    op.drop_column('guests', 'is_deleted')
