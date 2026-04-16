# import de libs third-party
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import paginate as sa_paginate
from sqlalchemy.orm import Session

# import do current-app
from app.core.config import get_db
from app.schemas.api_keys import CreateApiKeySchema
from app.services.api_key_service import ApiKeyService
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

    # consulta as chaves de api do hotel
    query = ApiKeyService.list_keys(db, hotel_id)

    # paginação
    params = Params(page=page, size=per_page)
    page_obj = sa_paginate(db, query, params)

    return render(
        templates,
        request,
        "dashboard/api_keys/api_keys.html",
        {
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

    api_key, raw_key, error = ApiKeyService.create_key(db, hotel_id, payload.name)
    if error:
        raise HTTPException(status_code=409, detail=error)

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

    api_key, error = ApiKeyService.toggle_key(db, api_key_id, hotel_id)
    if error:
        add_flash_message(request, error, "danger")
        return RedirectResponse(request.url_for("api_keys"), status_code=303)

    add_flash_message(request, "Chave atualizada com sucesso", "success")
    return RedirectResponse(request.url_for("api_keys"), status_code=303)