"""add audit logs


Revision ID: 875eed9f1379
Revises: 757e4fb18380
Create Date: 2026-02-06 16:18:17.511087

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '875eed9f1379'
down_revision: Union[str, Sequence[str], None] = '757e4fb18380'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('hotel_id', sa.Integer, sa.ForeignKey('hotels.id', ondelete='CASCADE'), nullable=False),
        sa.Column('collaborator_id', sa.Integer, sa.ForeignKey('collaborators.id', ondelete='SET NULL'), nullable=True),
        sa.Column('action', sa.String(length=255), nullable=False),
        sa.Column('entity', sa.String(length=255), nullable=False),
        sa.Column('entity_id', sa.Integer, nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('audit_logs')
