# import de libs built-in

# import de libs third-party
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import paginate as sa_paginate
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

# import do current-app
from app.core.config import get_db
from app.helpers.api_keys.create_key import generate_api_key, hash_api_key, create_key
from app.helpers.api_keys.update_key import update_key
from app.models.api_keys import ApiKey
from app.schemas.api_keys import CreateApiKeySchema
from app.utils.flash import add_flash_message, render
from app.utils.session_guard import require_admin_session

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

    # gera a chave e salva numa variavel
    raw_key = generate_api_key()
    # hashifica a chave para salvar no banco
    key_hash = hash_api_key(raw_key)
    # salva no banco
    create_key(db, hotel_id, payload.name, key_hash)

    # retorna a resposta em json com a variavel da chave.
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
    
    update_key(db, key, request)
    
    return RedirectResponse("/dashboard_api_keys", status_code=303)
