from xmlrpc.client import DateTime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, func
from core.config import Base

class Services(Base):
    __tablename__ = "services_requests"

    id = Column(Integer, primary_key=True, index=True)
    reservation_id = Column(Integer, ForeignKey('reservations.id', ondelete='cascade'), nullable=False)
    guest_id = Column(Integer, ForeignKey('guests.id', ondelete='cascade'), nullable=False)
    room_id = Column(Integer, ForeignKey('rooms.id', ondelete='cascade'), nullable=False)
    request = Column(String(500), nullable=False)
    status = Column(Enum('pending', 'in_progress', 'completed'), nullable=False, server_default='available')
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)