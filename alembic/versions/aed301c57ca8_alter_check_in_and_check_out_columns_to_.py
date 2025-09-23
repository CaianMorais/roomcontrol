"""alter check_in and check_out columns to DateTime

Revision ID: aed301c57ca8
Revises: e53090f97bc5
Create Date: 2025-09-23 15:21:58.152969

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = 'aed301c57ca8'
down_revision: Union[str, Sequence[str], None] = 'e53090f97bc5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Alterando a coluna 'check_in' de Date para DateTime
    op.alter_column('reservations', 'check_in',
                    existing_type=sa.Date(),
                    type_=sa.DateTime(),
                    existing_nullable=False)

    # Alterando a coluna 'check_out' de Date para DateTime
    op.alter_column('reservations', 'check_out',
                    existing_type=sa.Date(),
                    type_=sa.DateTime(),
                    existing_nullable=False)


def downgrade() -> None:
    op.alter_column('reservations', 'check_in',
                    existing_type=sa.DateTime(),
                    type_=sa.Date(),
                    existing_nullable=False)

    op.alter_column('reservations', 'check_out',
                    existing_type=sa.DateTime(),
                    type_=sa.Date(),
                    existing_nullable=False)
