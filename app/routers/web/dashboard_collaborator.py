# import de libs padrão
from typing import Optional

# import de libs third-party
from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import paginate as sa_paginate
from sqlalchemy.orm import Session

# import do current-app
from app.core.config import get_db
from app.core.security import generate_csrf_token, validate_csrf_token
from app.services.collaborator_service import CollaboratorService
from app.utils.flash import add_flash_message, render
from app.utils.session_guard import require_admin_session

# configuração do router e templates
router = APIRouter(
    prefix="/dashboard_collaborators",
    tags=["collaborators"],
    dependencies=[Depends(require_admin_session)]
)
templates = Jinja2Templates(directory="app/templates")

###### ROTAS PARA PÁGINAS DE COLABORADORES NO DASHBOARD ######

@router.get("", response_class=HTMLResponse, include_in_schema=False)
def collaborators(
    request: Request,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=200),
    search: Optional[str] = Query(""),
    status: Optional[str] = Query(None),
):
    hotel_id = request.session.get("hotel_id")

    has_filter = False
    query = CollaboratorService.list_collaborators(db, hotel_id)

    if search or status:
        query = CollaboratorService.filter_collaborators(query, search, status)
        has_filter = True

    params = Params(page=page, size=per_page)
    page_obj = sa_paginate(db, query, params)

    return render(
        templates,
        request,
        "dashboard/collaborators/collaborators.html",
        {
            "collaborators": page_obj.items,
            "has_filter": has_filter,
            "search": search,
            "status": status,
            "pager": {
                "page": page_obj.page,
                "pages": page_obj.pages,
                "per_page": page_obj.size,
                "total": page_obj.total,
            },
        }
    )


@router.get("/new", response_class=HTMLResponse, include_in_schema=False)
def new_collaborator(request: Request):
    csrf_token = generate_csrf_token(request)
    return render(
        templates,
        request,
        "dashboard/collaborators/form_collaborator.html",
        {"csrf_token": csrf_token}
    )


@router.post("/create", response_class=HTMLResponse, include_in_schema=False)
def create_collaborator(
    request: Request,
    db: Session = Depends(get_db),
    csrf_token: str = Form(...),
    firstname: str = Form(...),
    lastname: str = Form(...),
    cpf: str = Form(...),
    username: str = Form(...)
):
    if not validate_csrf_token(request, csrf_token):
        add_flash_message(request, "Token de segurança inválido", "danger")
        return RedirectResponse(url=request.url_for('new_collaborator'), status_code=303)

    hotel_id = request.session.get("hotel_id")

    collaborator, outcome, error = CollaboratorService.create_collaborator(db, hotel_id, firstname, lastname, username, cpf)
    # outcome para saber se é novo, restaurado ou já existente (para uso futuro)

    if error:
        add_flash_message(request, error, "danger")
        return RedirectResponse(url=request.url_for('new_collaborator'), status_code=303)

    add_flash_message(request, "Colaborador cadastrado, no primeiro acesso a senha é o CPF.", "success")

    return RedirectResponse(url=request.url_for('edit_collaborator', collaborator_id=collaborator.id), status_code=303)


@router.get("/edit/{collaborator_id}", response_class=HTMLResponse, include_in_schema=False)
def edit_collaborator(
    collaborator_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    hotel_id = request.session.get("hotel_id")

    collaborator, error = CollaboratorService.get_collaborator(db, collaborator_id, hotel_id)
    if error:
        add_flash_message(request, error, "warning")
        return RedirectResponse(url=request.url_for('collaborators'), status_code=303)

    csrf_token = generate_csrf_token(request)
    return render(
        templates,
        request,
        "dashboard/collaborators/form_collaborator.html",
        {
            "collaborator": collaborator,
            "csrf_token": csrf_token
        }
    )


@router.post("/edit/{collaborator_id}", response_class=HTMLResponse, include_in_schema=False)
def update_collaborator(
    request: Request,
    collaborator_id: int,
    firstname: str = Form(...),
    lastname: str = Form(...),
    username: str = Form(...),
    is_active: Optional[bool] = Form(False),
    change_password: Optional[bool] = Form(False),
    csrf_token: str = Form(...),
    db: Session = Depends(get_db)
):
    if not validate_csrf_token(request, csrf_token):
        add_flash_message(request, "Token de segurança inválido, operação finalizada.", "danger")
        return RedirectResponse(url=request.url_for('collaborators'), status_code=303)

    hotel_id = request.session.get("hotel_id")
    if not hotel_id:
        add_flash_message(request, "Hotel não reconhecido", "warning")
        return RedirectResponse(url=request.url_for('collaborators'), status_code=303)

    collaborator, error = CollaboratorService.get_collaborator(db, collaborator_id, hotel_id)
    if error:
        add_flash_message(request, error, "warning")
        return RedirectResponse(url=request.url_for('collaborators'), status_code=303)

    CollaboratorService.update_collaborator(db, collaborator, firstname, lastname, username, is_active, change_password)

    if change_password:
        add_flash_message(request, "Senha redefinida, e deverá ser trocada no próximo login.", "info")

    add_flash_message(request, "Colaborador editado com sucesso", "success")
    return RedirectResponse(url=request.url_for('edit_collaborator', collaborator_id=collaborator.id), status_code=303)


@router.get("/delete/{collaborator_id}", response_class=HTMLResponse, include_in_schema=False)
def delete_collaborator(
    request: Request,
    collaborator_id: int,
    db: Session = Depends(get_db)
):
    hotel_id = request.session.get("hotel_id")

    collaborator, error = CollaboratorService.delete_collaborator(db, collaborator_id, hotel_id)
    if error:
        add_flash_message(request, error, "warning")
        return RedirectResponse(url=request.url_for('collaborators'), status_code=303)

    add_flash_message(request, "Colaborador deletado com sucesso", "success")
    return RedirectResponse(url=request.url_for('collaborators'), status_code=303)