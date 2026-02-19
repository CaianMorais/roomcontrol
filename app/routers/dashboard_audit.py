# import de libs padrao
import datetime
from typing import List, Optional

#import de libs third-party

from fastapi import APIRouter, HTTPException, Depends, Form, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import paginate as sa_paginate
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_

# import de funções da aplicação local

from app.core.config import get_db
from app.core.security import generate_csrf_token, validate_csrf_token
from app.core.dependencies import get_api_hotel
from app.helpers.guests.guest_delete import guest_delete
from app.helpers.guests.guest_updater import guest_updater
from app.helpers.guests.guest_creator import guest_creator
from app.helpers.verify_guest import verify_guest_by_id
from app.utils.flash import add_flash_message, render
from app.utils.session_guard import require_session
from app.schemas.guest import GuestOut
from app.models.audit_log import AuditLog
from app.models.collaborator import Collaborator
from app.helpers.guests.subquery_reservations import subquery_reservations
from app.helpers.guests.filter_guests import filter_guests
from app.helpers.guests.restore_guest import restore_guest

router = APIRouter(
    prefix="/dashboard_audit",
    tags=["audit"],
    dependencies=[Depends(require_session)]
)

api_router = APIRouter(
    prefix="/api",
    tags=["audit"],
    dependencies=[Depends(get_api_hotel)]
)

templates = Jinja2Templates(directory="app/templates")

@router.get("", response_class=HTMLResponse, include_in_schema=False)
def audit(
    request: Request,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=200),
    name: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    entity: Optional[str] = Query(None),
    entity_id: Optional[str] = Query(None),
    before: Optional[str] = Query(None),
    after: Optional[str] = Query(None),
):
    hotel_id = request.session.get("hotel_id")
    has_filter = False

    query = db.query(AuditLog, Collaborator) \
    .filter(AuditLog.hotel_id == hotel_id) \
    .join(Collaborator, Collaborator.id == AuditLog.collaborator_id) \
    .order_by(AuditLog.id.desc())

    if name:
        has_filter = True
        query = query.filter(
            or_(Collaborator.firstname.ilike(f"%{name}%"),
                Collaborator.lastname.ilike(f"%{name}%")
                )
            )
        
    if action:
        has_filter = True
        query = query.filter(AuditLog.action == action)

    if entity:
        has_filter = True
        query = query.filter(AuditLog.entity == entity)

    if entity_id:
        try:
            has_filter = True
            entity_id = int(entity_id)
            query = query.filter(AuditLog.entity_id == entity_id)
        except ValueError:
            add_flash_message(request, "Erro ao pesquisar identificador", "warning")
            return RedirectResponse(url='/dashboard_audit', status_code=303)
        
    if before:
        has_filter = True
        query = query.filter(AuditLog.created_at <= before)
    
    if after:
        has_filter = True
        query = query.filter(AuditLog.created_at >= after)

    params = Params(page=page, size=per_page)
    page_obj = sa_paginate(db, query, params)

    return render(
        templates,
        request,
        "dashboard/audit/audit.html",
        {
            "request": request,
            "has_filter": has_filter,
            "logs": page_obj.items,
            "pager": {
                "page": page_obj.page,
                "pages": page_obj.pages,
                "per_page": page_obj.size,
                "total": page_obj.total,
            },
            "name" : name,
            "action": action,
            "entity": entity,
            "entity_id": entity_id,
            "before": before,
            "after": after
        }
    )

