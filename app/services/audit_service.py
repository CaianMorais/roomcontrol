from typing import Optional
from sqlalchemy.orm import Session

from app.repositories.audit_repository import AuditRepository


class AuditService:

    @staticmethod
    def list_logs(db: Session, hotel_id: int):
        return AuditRepository.base_query(db, hotel_id)

    @staticmethod
    def filter_logs(
        query,
        name: Optional[str] = None,
        action: Optional[str] = None,
        entity: Optional[str] = None,
        entity_id: Optional[str] = None,
        before: Optional[str] = None,
        after: Optional[str] = None,
    ):
        return AuditRepository.apply_filters(query, name, action, entity, entity_id, before, after)

    @staticmethod
    def register(
        db: Session,
        hotel_id: int,
        action: str,
        entity: str,
        entity_id: int,
        collaborator_id: Optional[int] = None,
    ):
        AuditRepository.create(db, hotel_id, action, entity, entity_id, collaborator_id)