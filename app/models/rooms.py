from sqlalchemy import Column, Integer, String, Boolean, DateTime, func, ForeignKey, Float, Enum, Text
from app.core.config import Base

# op.create_table(
#     'rooms',
#     sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
#     sa.Column('hotel_id', sa.Integer, sa.ForeignKey('hotels.id', ondelete="CASCADE"), nullable=False),
#     sa.Column('room_number', sa.String(20), nullable=False),
#     sa.Column('type', sa.String(50), nullable=False),
#     sa.Column('capacity_adults', sa.Integer, nullable=True),
#     sa.Column('capacity_children', sa.Integer, nullable=True),
#     sa.Column('capacity_total', sa.Integer, nullable=True),
#     sa.Column('price', sa.Float, nullable=True),
#     sa.Column('status', sa.Enum('available', 'occupied', 'maintenance'), nullable=False, server_default='available'),
#     sa.Column('comments', sa.Text, nullable=True),
#     sa.Column('created_at', sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
#     sa.Column('updated_at', sa.TIMESTAMP, server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
# )

class Rooms(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False)
    room_number = Column(String(20), nullable=False)
    type = Column(String(50), nullable=False)
    capacity_adults = Column(Integer, nullable=True)
    capacity_children = Column(Integer, nullable=True)
    capacity_total = Column(Integer, nullable=True)
    price = Column(Float, nullable=True)
    status = Column(Enum('available', 'occupied', 'maintenance'), nullable=False, server_default='available')
    comments = Column(Text, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)