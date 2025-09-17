from xmlrpc.client import DateTime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from app.core.config import Base

class Guest(Base):
    __tablename__ = "guests"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)
    phone_number = Column(String(20), index=True, nullable=True)
    cpf = Column(String(14), unique=True, index=True, nullable=False)
    hotel_id = Column(Integer, ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
