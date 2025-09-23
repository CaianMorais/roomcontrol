from sqlalchemy import Column, Integer, String, DateTime, func, Boolean, ForeignKey
from app.core.config import Base

# op.create_table(
#     'reservations',
#     sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
#     sa.Column('guest_id', sa.Integer, sa.ForeignKey('guests.id', ondelete="CASCADE"), nullable=False),
#     sa.Column('room_id', sa.Integer, sa.ForeignKey('rooms.id', ondelete="CASCADE"), nullable=False),
#     sa.Column('check_in', sa.Date, nullable=False),
#     sa.Column('check_out', sa.Date, nullable=False),
#     sa.Column('status', sa.Enum('booked', 'checked_in', 'checked_out', 'canceled'), nullable=False, server_default='booked'),
#     sa.Column('created_at', sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
#     sa.Column('updated_at', sa.TIMESTAMP, server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
# )

class Reservations(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    guest_id = Column(Integer, ForeignKey("guests.id", ondelete="CASCADE"), nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False)
    check_in = Column(DateTime, nullable=False)
    check_out = Column(DateTime, nullable=False)
    status = Column(String(50), nullable=False, default='booked')
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)