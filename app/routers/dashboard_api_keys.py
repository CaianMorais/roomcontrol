# import de libs padrao
import datetime
from typing import List, Optional

#import de libs third-party

from fastapi import APIRouter, HTTPException, Depends, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import paginate as sa_paginate
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

# import de funções da aplicação local

from app.core.config import get_db
from app.utils.flash import add_flash_message, render
from app.utils.session_guard import require_session, require_admin_session
from app.models.api_keys import ApiKey
from app.helpers.api_keys.create_key import generate_api_key, hash_api_key
from app.helpers.register_audit import register_audit
from app.schemas.api_keys import CreateApiKeySchema

router = APIRouter(
    prefix="/dashboard_api_keys",
    tags=["api_keys"],
    dependencies=[Depends(require_admin_session)]
)

templates = Jinja2Templates(directory="app/templates")

@router.get("", response_class=HTMLResponse, include_in_schema=False)
def api_keys(
    request: Request,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=200),
):
    hotel_id = request.session.get("hotel_id")
    if not hotel_id:
        add_flash_message(request, 'Hotel não reconhecido', 'warning')
        return RedirectResponse(url="/dashboard", status_code=303)
    
    query = db.query(ApiKey) \
        .filter(ApiKey.hotel_id == hotel_id) \
        .order_by(ApiKey.is_active.desc()) \
        .order_by(ApiKey.created_at.desc())
    
    params = Params(page=page, size=per_page)
    page_obj = sa_paginate(db, query, params)

    return render(
        templates,
        request,
        "dashboard/api_keys/api_keys.html",
        {
            "request": request,
            "keys": page_obj.items,
            "pager": {
                "page": page_obj.page,
                "pages": page_obj.pages,
                "per_page": page_obj.size,
                "total": page_obj.total,
            },
        }
    )

@router.post("/create", include_in_schema=False)
def create_api_key(
    request: Request,
    payload: CreateApiKeySchema,
    db: Session = Depends(get_db)
):
    hotel_id = request.session.get("hotel_id")
    if not hotel_id:
        raise HTTPException(status_code=401, detail="Não autenticado")

    raw_key = generate_api_key()
    key_hash = hash_api_key(raw_key)

    api_key = ApiKey(
        hotel_id=hotel_id,
        name=payload.name,
        key_hash=key_hash
    )

    try:
        db.add(api_key)
        db.commit()
        db.refresh(api_key)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Erro ao gerar API Key. Tente novamente."
        )

    # Auditoria (opcional, mas altamente recomendada)
    # register_audit(
    #     db=db,
    #     hotel_id=hotel_id,
    #     collaborator_id=request.session.get("collaborator_id"),
    #     action="create",
    #     entity="api_key",
    #     entity_id=api_key.id
    # )

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "api_key": raw_key,
            "message": "Guarde esta chave. Ela não poderá ser exibida novamente."
        }
    )

@router.get("/update/{api_key_id}", include_in_schema=False)
def update_api_key(
    request: Request,
    api_key_id: int,
    db: Session = Depends(get_db),
):
    hotel_id = request.session.get("hotel_id")

    if not hotel_id:
        add_flash_message(request, "Hotel não encontrado", "danger")
        return RedirectResponse(url="/dashboard", status_code=303)
    
    key = db.query(ApiKey) \
    .filter(ApiKey.id == api_key_id) \
    .filter(ApiKey.hotel_id == hotel_id) \
    .first()

    if not key:
        add_flash_message(request, "A chave não foi encontrada", "danger")
        return RedirectResponse(url="/dashboard_api_keys", status_code=303)
    
    try:
        if key.is_active:
            key.is_active = False
        else:
            key.is_active = True

        db.commit()
        db.refresh(key)
        add_flash_message(request, "Chave atualizada com sucesso", "success")
    except IntegrityError:
        db.rollback()
        add_flash_message(request, "Erro ao atualizar o status da chave", "danger")
        return RedirectResponse(url="/dashboard_api_keys", status_code=303)
    
    return RedirectResponse("/dashboard_api_keys", status_code=303)
