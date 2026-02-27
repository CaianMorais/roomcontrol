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

# import de funções da aplicação local

from app.core.config import get_db
from app.core.security import generate_csrf_token, validate_csrf_token
from app.core.dependencies import get_api_access
from app.helpers.guests.valid_phone_number import valid_phone_number_on_create, valid_phone_number_on_edit
from app.helpers.register_audit import register_audit
from app.utils.flash import add_flash_message, render
from app.utils.session_guard import require_session
from app.schemas.guest import GuestOut
from app.models.guest import Guest
from app.models.hotel import Hotel

from app.services.guest_service import GuestService

router = APIRouter(
    prefix="/dashboard_guests",
    tags=["guests"],
    dependencies=[Depends(require_session)]
)

api_router = APIRouter(
    prefix="/api",
    tags=["guests"],
    dependencies=[Depends(get_api_access)]
)

templates = Jinja2Templates(directory="app/templates")

@api_router.get("/guests", response_model=List[GuestOut], summary="Filtrar hóspedes")
def get_guests(
    access: dict = Depends(get_api_access),
    guest_cpf: Optional[str] = Query(None, description="Filtrar pelo CPF do hóspede"),
    guest_name: Optional[str] = Query(None, description="Filtrar pelo nome do hóspede"),
    hotel_id: Optional[str] = Query(None, description="Filtrar pelo ID do hotel (FUNCIONAL SOMENTE PARA CHAVE GLOBAL)"),
    hotel_name: Optional[str] = Query(None, description="Filtrar pelo nome do hotel (FUNCIONAL SOMENTE PARA CHAVE GLOBAL)"),
    db: Session = Depends(get_db)
):
    query = db.query(Guest).options(joinedload(Guest.hotel)) \
    .filter(Guest.is_deleted == False)

    if not access["is_global"]:
        query = query.filter(Guest.hotel_id == access["hotel_id"])

    else:
        if hotel_id:
            query = query.filter(Guest.hotel_id == hotel_id)
        if hotel_name:
            query = query.join(Hotel, Guest.hotel_id == Hotel.id) \
            .filter(Hotel.name.ilike(f"%{hotel_name}%"))

    if guest_cpf:
        query = query.filter(Guest.cpf.ilike(f"%{guest_cpf}%"))
    if guest_name:
        query = query.filter(Guest.name.ilike(f"%{guest_name}%"))

    guests = query.all()

    if not guests:
        raise HTTPException(status_code=404, detail="Nenhum hóspede encontrado")

    return guests


@router.get("", response_class=HTMLResponse, include_in_schema=False)
def guests(
    request: Request,
    db: Session = Depends(get_db),
    name: Optional[str] = Query("", description="Nome do hóspede"),
    cpf: Optional[str] = Query("", description="CPF do hóspede"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=200),
):
    
    # captura o hotel e inicia subquery
    has_filter = False
    hotel_id = request.session.get("hotel_id")

    # Service para listar os hóspedes
    query = GuestService.list_guests(db, hotel_id)

    # filtra os hospedes
    if name or cpf:
        has_filter = True
        query = GuestService.filter_guests(db, name, cpf, query)
        add_flash_message(request, "Filtro aplicado", "success")

    # paginação
    params = Params(page=page, size=per_page)
    page_obj = sa_paginate(db, query, params)

    return render(
        templates,
        request,
        "dashboard/guests/guests.html",
        {
            "request": request,
            "guests": page_obj.items,
            "has_filter": has_filter,
            "now": datetime.datetime.now(),
            "pager": {
                "page": page_obj.page,
                "pages": page_obj.pages,
                "per_page": page_obj.size,
                "total": page_obj.total,
            },
        }
    )

@router.get("/new", response_class=HTMLResponse, include_in_schema=False)
def new_guest(request: Request):
    csrf_token = generate_csrf_token(request)
    return render(
        templates,
        request,
        "dashboard/guests/new_guest.html",
        {
            "request": request,
            "csrf_token": csrf_token,
        }
    )

@router.post("/create_guest", response_class=HTMLResponse, include_in_schema=False)
def create_guest(
    request: Request,
    db: Session = Depends(get_db),
    name: str = Form(...),
    cpf: str = Form(...),
    email: str = Form(...),
    phone_number: str = Form(...),
    csrf_token: str = Form(...)
):
    print(phone_number)
    # valida o token
    if not validate_csrf_token(request, csrf_token):
        add_flash_message(request, "Token de segurança inválido.", "danger")
        return RedirectResponse(url=request.url_for("new_guest"), status_code=303)

    # pega o id do hotel na sessão e faz validações
    hotel_id = request.session.get("hotel_id")
    if not hotel_id or not name or not cpf:
        add_flash_message(request, "Erro ao cadastrar.", "danger")
        return RedirectResponse(url=request.url_for("new_guest"), status_code=303)

    # Service para criar o hóspede
    guest, error = GuestService.create_guest(
        db, hotel_id, name, cpf, email, phone_number
    )

    if error:
        add_flash_message(request, error, "danger")
        return RedirectResponse(request.url_for("new_guest"), status_code=303)

    # registra log
    register_audit(db, hotel_id, 'create', 'guest', guest.id, request.session.get("collaborator_id"))

    # validação do phone_number (não interrompe em caso não validação)
    valid_phone_number_on_create(request, phone_number)

    return RedirectResponse(
        url=request.url_for("edit_guest", guest_id=guest.id, guest_cpf=guest.cpf),
        status_code=303,
    )

@router.get('/edit/{guest_id}/{guest_cpf}', response_class=HTMLResponse, include_in_schema=False)
def edit_guest(
    guest_id: int,
    request: Request,
    next: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    # localiza hotel e o hospede
    hotel_id = request.session.get("hotel_id")
    guest = GuestService.get_guest(db, guest_id, hotel_id)

    # validações basicas 
    if not hotel_id or not guest:
        add_flash_message(request, "Erro ao localizar.", "danger")
        return RedirectResponse(url=request.url_for("guests"), status_code=303)
    
    csrf_token = generate_csrf_token(request)
    return render(
        templates,
        request,
        "dashboard/guests/edit_guest.html",
        {
            "guest": guest,
            "csrf_token": csrf_token,
            "next": next
        }
    )

@router.post('/edit/{guest_id}/{guest_cpf}', response_class=HTMLResponse, include_in_schema=False)
def update_guest(
    request: Request,
    guest_id: int,
    email: str = Form(...),
    phone_number: str = Form(...),
    csrf_token: str = Form(...),
    next: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    # captura o hotel
    hotel_id = request.session.get("hotel_id")

    # localiza o hospede
    guest = GuestService.get_guest(db, guest_id, hotel_id)

    # validações básicas
    if not validate_csrf_token(request, csrf_token):
        add_flash_message(request, "Token de segurança inválido.", "danger")
        return RedirectResponse(url=request.url_for("guests"), status_code=303)
    
    valid = valid_phone_number_on_edit(request, phone_number, guest)
    if not valid:
        return RedirectResponse(url=request.url_for("edit_guest", guest_id=guest.id, guest_cpf=guest.cpf), status_code=303)
    
    # atualiza o hospede com os novos dados recebidos
    GuestService.update_guest(db, guest, email, phone_number)
    add_flash_message(request, "Hóspede atualizado com sucesso", "success")

    # registra log
    register_audit(db, hotel_id, 'update', 'guest', guest.id, request.session.get("collaborator_id"))

    if next:
        return RedirectResponse(url=next, status_code=303)
    return RedirectResponse(url=request.url_for("guests"), status_code=303)

@router.get("/delete/{guest_id}/{guest_cpf}", response_class=HTMLResponse, include_in_schema=False)
def delete_guest(
    guest_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    # captura o hotel
    hotel_id = request.session.get("hotel_id")

    #localiza o hospede 
    guest = GuestService.get_guest(db, guest_id, hotel_id)
    
    # soft-delete na service
    GuestService.delete_guest(db, guest)
    add_flash_message(request, "Hóspede excluído com sucesso!", "success")

    # registra log
    register_audit(db, hotel_id, 'delete', 'guest', guest.id, request.session.get("collaborator_id"))

    return RedirectResponse(url=request.url_for("guests"), status_code=303)