"""create hotel management tables

Revision ID: 8ab502b9185e
Revises: f807ffdc28ad
Create Date: 2025-09-17 09:57:10.374709

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8ab502b9185e'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'hotels',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('login', sa.String(50), nullable=False, unique=True),
        sa.Column('password', sa.String(255), nullable=False),
        sa.Column('address', sa.String(255), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('state', sa.String(100), nullable=True),
        sa.Column('zip_code', sa.String(20), nullable=True),
        sa.Column('phone_number', sa.String(20), nullable=True),
        sa.Column('email', sa.String(100), nullable=True),
        sa.Column('cnpj', sa.String(20), nullable=False, unique=True),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP, server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    op.create_table(
        'rooms',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('hotel_id', sa.Integer, sa.ForeignKey('hotels.id', ondelete="CASCADE"), nullable=False),
        sa.Column('room_number', sa.String(20), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('capacity_adults', sa.Integer, nullable=True),
        sa.Column('capacity_children', sa.Integer, nullable=True),
        sa.Column('capacity_total', sa.Integer, nullable=True),
        sa.Column('price', sa.Float, nullable=True),
        sa.Column('status', sa.Enum('available', 'occupied', 'maintenance'), nullable=False, server_default='available'),
        sa.Column('comments', sa.Text, nullable=True),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP, server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    op.create_table(
        'guests',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('email', sa.String(100), nullable=True, unique=True),
        sa.Column('phone_number', sa.String(20), nullable=True, unique=True),
        sa.Column('cpf', sa.String(14), nullable=False, unique=True),
        sa.Column('hotel_id', sa.Integer, sa.ForeignKey('hotels.id', ondelete="CASCADE"), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP, server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    op.create_table(
        'reservations',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('guest_id', sa.Integer, sa.ForeignKey('guests.id', ondelete="CASCADE"), nullable=False),
        sa.Column('room_id', sa.Integer, sa.ForeignKey('rooms.id', ondelete="CASCADE"), nullable=False),
        sa.Column('check_in', sa.Date, nullable=False),
        sa.Column('check_out', sa.Date, nullable=False),
        sa.Column('status', sa.Enum('booked', 'checked_in', 'checked_out', 'canceled'), nullable=False, server_default='booked'),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP, server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    op.create_table(
        'services_requests',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('reservation_id', sa.Integer, sa.ForeignKey('reservations.id', ondelete="CASCADE"), nullable=False),
        sa.Column('guest_id', sa.Integer, sa.ForeignKey('guests.id', ondelete="CASCADE"), nullable=False),
        sa.Column('room_id', sa.Integer, sa.ForeignKey('rooms.id', ondelete="CASCADE"), nullable=False),
        sa.Column('request', sa.Text, nullable=False),
        sa.Column('status', sa.Enum('pending', 'in_progress', 'completed'), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP, server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    op.drop_table('services_requests')
    op.drop_table('reservations')
    op.drop_table('guests')
    op.drop_table('rooms')
    op.drop_table('hotels')

    # Dropar enums
    op.execute("DROP TYPE IF EXISTS status")
    op.execute("DROP TYPE IF EXISTS reservation_status")
    op.execute("DROP TYPE IF EXISTS service_request_status")
    # ### end Alembic commands ###