"""add collaborators

Revision ID: 757e4fb18380
Revises: 8a4a56a9d6cb
Create Date: 2026-02-06 14:55:08.917890

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '757e4fb18380'
down_revision: Union[str, Sequence[str], None] = '8a4a56a9d6cb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'collaborators',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('firstname', sa.String(length=255), nullable=False),
        sa.Column('lastname', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=False),
        sa.Column('cpf', sa.String(11), nullable=False),
        sa.Column('hotel_id', sa.Integer, sa.ForeignKey('hotels.id', ondelete='CASCADE'), nullable=False),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.Column('is_deleted', sa.Boolean, nullable=False, default=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

def downgrade() -> None:
    op.drop_table('collaborators')
