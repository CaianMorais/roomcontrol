# import de libs built-in
from typing import Optional

# import de libs third-party
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import paginate as sa_paginate
from sqlalchemy import or_
from sqlalchemy.orm import Session

# import do current-app
from app.core.config import get_db
from app.core.dependencies import get_api_hotel
from app.helpers.audit.filter_logs import filter_logs
from app.models.audit_log import AuditLog
from app.models.collaborator import Collaborator
from app.utils.flash import add_flash_message, render
from app.utils.session_guard import require_admin_session

router = APIRouter(
    prefix="/dashboard_audit",
    tags=["audit"],
    dependencies=[Depends(require_admin_session)]
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

    if not hotel_id:
        add_flash_message(request, "Hotel não localizado", 'danger')
        return RedirectResponse(url='/dashboard', status_code=303)

    has_filter = False

    query = db.query(AuditLog, Collaborator) \
    .filter(AuditLog.hotel_id == hotel_id) \
    .join(Collaborator, Collaborator.id == AuditLog.collaborator_id) \
    .order_by(AuditLog.id.desc())

    if name or action or entity or entity_id or before or after:
        query = filter_logs(request, query, name, action, entity, entity_id, before, after)
        has_filter = True

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

