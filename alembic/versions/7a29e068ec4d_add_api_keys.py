"""add api keys

Revision ID: 7a29e068ec4d
Revises: 875eed9f1379
Create Date: 2026-02-06 16:18:43.526433

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a29e068ec4d'
down_revision: Union[str, Sequence[str], None] = '875eed9f1379'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'api_keys',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('hotel_id', sa.Integer, sa.ForeignKey('hotels.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('key_hash', sa.String(length=255), nullable=False, unique=True),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.Column('last_used_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('api_keys')
