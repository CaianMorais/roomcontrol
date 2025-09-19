"""add is_active to hotels and rooms

Revision ID: e53090f97bc5
Revises: 8ab502b9185e
Create Date: 2025-09-19 15:06:34.753315

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = 'e53090f97bc5'
down_revision: Union[str, Sequence[str], None] = '8ab502b9185e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # op.add_column(
    #     "hotels",
    #     sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true())
    # )
    # op.add_column(
    #     "rooms",
    #     sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true())
    # )

    op.execute("""
        ALTER TABLE hotels 
        ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT true 
        AFTER cnpj
    """)
    
    op.execute("""
        ALTER TABLE rooms 
        ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT true 
        AFTER comments
    """)

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("rooms", "is_active")
    op.drop_column("hotels", "is_active")