from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.audit_log import AuditLog
from app.models.collaborator import Collaborator


class AuditRepository:

    @staticmethod
    def base_query(db: Session, hotel_id: int):
        return (
            db.query(AuditLog, Collaborator)
            .filter(AuditLog.hotel_id == hotel_id)
            .outerjoin(Collaborator, Collaborator.id == AuditLog.collaborator_id)
            .order_by(AuditLog.id.desc())
        )

    @staticmethod
    def apply_filters(
        query,
        name: Optional[str] = None,
        action: Optional[str] = None,
        entity: Optional[str] = None,
        entity_id: Optional[str] = None,
        before: Optional[str] = None,
        after: Optional[str] = None,
    ):
        if name:
            query = query.filter(
                or_(
                    Collaborator.firstname.ilike(f"%{name}%"),
                    Collaborator.lastname.ilike(f"%{name}%")
                )
            )

        if action:
            query = query.filter(AuditLog.action == action)

        if entity:
            query = query.filter(AuditLog.entity == entity)

        if entity_id is not None:
            try:
                query = query.filter(AuditLog.entity_id == int(entity_id))
            except ValueError:
                return None, "Erro ao pesquisar identificador: valor inválido."

        if before:
            query = query.filter(AuditLog.created_at <= before)

        if after:
            query = query.filter(AuditLog.created_at >= after)

        return query, None

    @staticmethod
    def create(
        db: Session,
        hotel_id: int,
        action: str,
        entity: str,
        entity_id: int,
        collaborator_id: Optional[int] = None,
    ):
        log = AuditLog(
            hotel_id=hotel_id,
            collaborator_id=collaborator_id,
            action=action,
            entity=entity,
            entity_id=entity_id,
        )
        db.add(log)
        db.commit()