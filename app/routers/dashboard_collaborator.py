# import de libs padrao
import datetime
from typing import List, Optional

#import de libs third-party

from fastapi import APIRouter, HTTPException, Depends, Form, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import paginate as sa_paginate
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_

# import de funções da aplicação local

from app.core.config import get_db
from app.core.security import generate_csrf_token, validate_csrf_token
from app.helpers.guests.guest_delete import guest_delete
from app.helpers.guests.guest_updater import guest_updater
from app.helpers.guests.guest_creator import guest_creator
from app.helpers.verify_guest import verify_guest_by_id
from app.utils.flash import add_flash_message, render
from app.utils.session_guard import require_session
from app.schemas.guest import GuestOut
from app.models.collaborator import Collaborator
from app.helpers.guests.subquery_reservations import subquery_reservations
from app.helpers.guests.filter_guests import filter_guests
from app.helpers.guests.restore_guest import restore_guest
from app.helpers.api_keys.create_key import generate_api_key, hash_api_key
from app.helpers.register_audit import register_audit
from app.schemas.api_keys import CreateApiKeySchema
from app.core.security import hash_password
from app.core.dependencies import get_api_hotel

router = APIRouter(
    prefix="/dashboard_collaborators",
    tags=["collaborators"],
    dependencies=[Depends(require_session)]
)

api_router = APIRouter(
    prefix="/api",
    tags=["collaborators"],
    dependencies=[Depends(get_api_hotel)]
)

templates = Jinja2Templates(directory="app/templates")

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

    query = db.query(Collaborator) \
    .filter(Collaborator.hotel_id == hotel_id) \
    .filter(Collaborator.is_deleted == False) \
    .order_by(Collaborator.is_active) \
    .order_by(Collaborator.created_at.desc()) \

    if search:
        query = query.filter(
            or_(Collaborator.cpf.ilike(f"%{search}%"),
                Collaborator.firstname.ilike(f"%{search}%"),
                Collaborator.lastname.ilike(f"%{search}%")
            )
        )
        has_filter=True

    if status == "active":
        query = query.filter(Collaborator.is_active == True)
        has_filter = True

    elif status == "inactive":
        query = query.filter(Collaborator.is_active == False)
        has_filter = True

    params = Params(page=page, size=per_page)
    page_obj = sa_paginate(db, query, params)

    return render(
        templates,
        request,
        "dashboard/collaborators/collaborators.html",
        {
            "request": request,
            "collaborators": page_obj.items,
            "has_filter" : has_filter,
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
def new_collaborator(
    request: Request,
):
    csrf_token = generate_csrf_token()

    return render(
        templates,
        request,
        "dashboard/collaborators/new_collaborator.html",
        {
            "csrf_token": csrf_token
        }
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
    if not validate_csrf_token(csrf_token):
        add_flash_message(request, "Token de segurança inválido", "danger")
        return RedirectResponse(url="/dashboard_collaborators/new", status_code=303)
    
    hotel_id = request.session.get("hotel_id")

    if username == "" or not username:
        username = f"{firstname.lower().strip()}.{lastname.lower().strip()}"

    collaborator = db.query(Collaborator) \
    .filter(Collaborator.cpf == cpf) \
    .first()

    if collaborator is not None and collaborator.is_deleted == False:
        add_flash_message(request, "Esse colaborador já está cadastrado no seu hotel", "danger")
        return RedirectResponse(url="/dashboard_guests/new", status_code=303)
    
    elif collaborator is not None and collaborator.is_deleted == True:
        collaborator.firstname = firstname
        collaborator.lastname = lastname
        collaborator.username = username
        collaborator.is_deleted = False
        collaborator.is_active = True

        db.commit()
        db.refresh(collaborator)

    elif collaborator is None:
        new_collaborator = Collaborator(
            firstname = firstname,
            lastname = lastname,
            username = username,
            cpf = cpf,
            hotel_id = hotel_id,
            password = hash_password(cpf),
            change_password = True
        )

        db.add(new_collaborator)
        db.commit()
        db.refresh(new_collaborator)

        add_flash_message(request, "Colaborador cadastrado, no primeiro acesso a senha é o CPF.", "success")

    return RedirectResponse(url="/dashboard_collaborators", status_code=303)

@router.get("/edit/{collaborator_id}", response_class=HTMLResponse, include_in_schema=False)
def edit_collaborator(
    collaborator_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    hotel_id = request.session.get("hotel_id")
        
    collaborator = db.query(Collaborator) \
    .filter(Collaborator.id == collaborator_id) \
    .filter(Collaborator.hotel_id == hotel_id) \
    .first()

    csrf_token = generate_csrf_token()

    return render(
        templates,
        request,
        "dashboard/collaborators/new_collaborator.html",
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
    print(change_password)
    # valida token
    if not validate_csrf_token(csrf_token):
        add_flash_message(request, "Token de segurança invéliado, operação finalizada.", "danger")
        return RedirectResponse(url="/dashboard", status_code=303)
    
    # captura o hotel
    hotel_id = request.session.get("hotel_id")

    # valida o hotel
    if not hotel_id:
        add_flash_message(request, "Hotel não reconhecido", "warning")
        return RedirectResponse(url="/dashboard_collaborators", status_code=303)
    
    #verificar se colaborador existe
    collaborator = db.query(Collaborator) \
    .filter(Collaborator.id == collaborator_id) \
    .filter(Collaborator.hotel_id == hotel_id) \
    .filter(Collaborator.is_deleted == False) \
    .first()

    # valida que o colaborador existe
    if not collaborator:
        add_flash_message(request, "Colaborador não encontrado", "warning")
        return RedirectResponse(url="/dashboard_collaborators", status_code=303)
    
    # se username for vazio, predefine nome + sobrenome
    if username == "" or not username:
        username = f"{firstname.lower().strip()}.{lastname.lower().strip()}"

    # se for redefinir senha define padrão o cpf
    if change_password:
        collaborator.password = hash_password(collaborator.cpf)
        add_flash_message(request, "Senha redefinida, e deverá ser trocada no próximo login.", "warning")

    collaborator.firstname = firstname
    collaborator.lastname = lastname
    collaborator.username = username
    collaborator.is_active = is_active
    collaborator.change_password = change_password

    db.commit()
    db.refresh(collaborator)

    add_flash_message(request, "Colaborador editado com sucesso", "success")
    return RedirectResponse(url="/dashboard_collaborators", status_code=303)

@router.get("/delete/{collaborator_id}", response_class=HTMLResponse, include_in_schema=False)
def delete_collaborator(
    request: Request,
    collaborator_id: int,
    db: Session = Depends(get_db)
):
    hotel_id = request.session.get("hotel_id")
    collaborator = db.query(Collaborator) \
    .filter(Collaborator.id == collaborator_id) \
    .filter(Collaborator.is_deleted == False) \
    .filter(Collaborator.hotel_id == hotel_id) \
    .first()

    collaborator.is_deleted = True
    db.commit()

    add_flash_message(request, "Colaborador deletado com sucesso", "success")
    return RedirectResponse(url="/dashboard_collaborators", status_code=303)

