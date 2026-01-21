from xmlrpc.client import DateTime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func, Boolean
from app.core.config import Base
from sqlalchemy.orm import relationship

class Guest(Base):
    __tablename__ = "guests"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), index=True, nullable=True)
    phone_number = Column(String(20), index=True, nullable=True)
    cpf = Column(String(14), unique=True, index=True, nullable=False)
    hotel_id = Column(Integer, ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)

    reservations = relationship("Reservations", back_populates="guest")
    hotel = relationship("Hotel", back_populates="guests")
