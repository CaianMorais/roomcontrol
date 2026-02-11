from xmlrpc.client import DateTime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func, Boolean
from app.core.config import Base
from sqlalchemy.orm import relationship


class Collaborator(Base):
    __tablename__ = "collaborators"

    id = Column(Integer, primary_key=True, index=True)
    firstname = Column(String(255), nullable=False)
    lastname = Column(String(255), nullable=False)
    username = Column(String(255), index=True, nullable=False)
    cpf = Column(String(14), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    change_password = Column(Boolean, default=True, nullable=False)
    hotel_id = Column(Integer, ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    audit_logs = relationship("AuditLog", back_populates='collaborator')
    hotel = relationship("Hotel", back_populates="collaborator")