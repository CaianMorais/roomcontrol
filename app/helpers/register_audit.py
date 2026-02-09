from app.models.audit_log import AuditLog

def register_audit(db, hotel_id:int, action: str, entity: str, entity_id: int, collaboratior_id: int | None = None):
    log = AuditLog(
        hotel_id=hotel_id,
        collaborator_id=collaboratior_id,
        action=action,
        entity=entity,
        entity_id=entity_id
    )
    
    db.add(log)
    db.commit()
