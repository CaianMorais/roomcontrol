"""add allow_service_requests to reservations

Revision ID: 8a4a56a9d6cb
Revises: a45c632f01eb
Create Date: 2026-01-19 14:53:10.064061

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8a4a56a9d6cb'
down_revision: Union[str, Sequence[str], None] = 'a45c632f01eb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'reservations',
        sa.Column(
            'allow_request_services',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('1')
        )
    )

def downgrade() -> None:
    op.drop_column(
        'reservations',
        'allow_request_services'
    )
