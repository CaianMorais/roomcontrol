from app.utils.flash import add_flash_message
from app.models.collaborator import Collaborator
from app.models.audit_log import AuditLog
from sqlalchemy import or_
from fastapi.responses import RedirectResponse

def filter_logs(request, query, name, action, entity, entity_id, before, after):
    if name:
        query = query.filter(
            or_(Collaborator.firstname.ilike(f"%{name}%"),
                Collaborator.lastname.ilike(f"%{name}%")
                )
            )
        
    if action:
        query = query.filter(AuditLog.action == action)

    if entity:
        query = query.filter(AuditLog.entity == entity)

    if entity_id:
        try:
            entity_id = int(entity_id)
            query = query.filter(AuditLog.entity_id == entity_id)
        except ValueError:
            add_flash_message(request, "Erro ao pesquisar identificador", "warning")
            return RedirectResponse(url='/dashboard_audit', status_code=303)
        
    if before:
        query = query.filter(AuditLog.created_at <= before)
    
    if after:
        query = query.filter(AuditLog.created_at >= after)

    return query