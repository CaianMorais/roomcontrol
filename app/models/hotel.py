from sqlalchemy import Column, Integer, String, DateTime, func, Boolean
from app.core.config import Base
from sqlalchemy.orm import relationship

class Hotel(Base):
    __tablename__ = "hotels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    login = Column(String(50), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    address = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    zip_code = Column(String(20), nullable=True)
    phone_number = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    cnpj = Column(String(20), nullable=False, unique=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    guests = relationship("Guest", back_populates="hotel")
    rooms = relationship("Rooms", back_populates="hotel")
    api_keys = relationship("ApiKey", back_populates="hotel")
    audit_logs = relationship("AuditLog", back_populates="hotel")
    collaborator = relationship("Collaborator", back_populates="hotel")