from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.core.config import Base

class AuditLog(Base):
    __tablename__ = 'audit_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    hotel_id = Column(
        Integer,
        ForeignKey('hotels.id', ondelete='CASCADE'),
        nullable=False
    )
    collaborator_id = Column(
        Integer,
        ForeignKey('collaborators.id', ondelete='SET NULL'),
        nullable=True
    )
    action = Column(String(255), nullable=False)
    entity = Column(String(255), nullable=False)
    entity_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    hotel = relationship("Hotel", back_populates="audit_logs")
    collaborator = relationship("Collaborator", back_populates="audit_logs")