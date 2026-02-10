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
from app.core.dependencies import get_api_hotel
from app.helpers.guests.guest_delete import guest_delete
from app.helpers.guests.guest_updater import guest_updater
from app.helpers.guests.guest_creator import guest_creator
from app.helpers.verify_guest import verify_guest_by_id
from app.utils.flash import add_flash_message, render
from app.utils.session_guard import require_session
from app.schemas.guest import GuestOut
from app.models.guest import Guest
from app.helpers.guests.subquery_reservations import subquery_reservations
from app.helpers.guests.filter_guests import filter_guests
from app.helpers.guests.restore_guest import restore_guest

router = APIRouter(
    prefix="/dashboard_guests",
    tags=["guests"],
    dependencies=[Depends(require_session)]
)

api_router = APIRouter(
    prefix="/api",
    tags=["guests"],
    dependencies=[Depends(get_api_hotel)]
)

templates = Jinja2Templates(directory="app/templates")

@api_router.get("/guests", response_model=List[GuestOut], summary="Filtrar hóspedes")
def get_guests(
    guest_cpf: Optional[str] = Query(None, description="Filtrar pelo CPF do hóspede"),
    guest_name: Optional[str] = Query(None, description="Filtrar pelo nome do hóspede"),
    hotel_id: Optional[str] = Query(None, description="Filtrar pelo ID do hotel"),
    db: Session = Depends(get_db)
):
    query = db.query(Guest).options(joinedload(Guest.hotel)).filter(Guest.is_deleted == False)

    if hotel_id:
        query = query.filter(Guest.hotel_id == hotel_id)
    if guest_cpf:
        query = query.filter(Guest.cpf == guest_cpf)
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
    has_filter = False
    hotel_id = request.session.get("hotel_id")
    subquery = subquery_reservations(db)

    query = db.query(
        Guest,
        subquery.c.reservation_check_in,
        subquery.c.reservation_status,
        subquery.c.reservation_id
    ).outerjoin(
        subquery,
        Guest.id == subquery.c.guest_id
    ).filter(Guest.hotel_id == hotel_id, Guest.is_deleted == False)

    if name or cpf:
        has_filter = True
        query = filter_guests(request, name, cpf, query)

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
def new_guest(request: Request, db: Session = Depends(get_db)):
    csrf_token = generate_csrf_token()
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
    if not validate_csrf_token(csrf_token):
        add_flash_message(request, "Token de segurança inválido", "danger")
        return RedirectResponse(url="/dashboard_guests/new", status_code=status.HTTP_303_SEE_OTHER)

    hotel_id = request.session.get("hotel_id")
    guest = db.query(Guest).filter(Guest.cpf == cpf).filter(Guest.hotel_id == hotel_id).first()

    if guest is not None and guest.is_deleted == False:
        add_flash_message(request, "CPF já cadastrado no seu hotel", "danger")
        return RedirectResponse(url="/dashboard_guests/new", status_code=303)
    
    elif guest is not None and guest.is_deleted == True:
        restore_guest(request, db, name, email, cpf, phone_number, hotel_id)
    
    elif guest is None:
        guest = guest_creator(request, name, cpf, email, phone_number, hotel_id, db)

    return RedirectResponse(
        url=f"/dashboard_reservations/new?guest_id={guest.id}",
        status_code=303,
    )

@router.get('/edit/{guest_id}/{guest_cpf}', response_class=HTMLResponse, include_in_schema=False)
def edit_guest(
    guest_id: int,
    request: Request,
    next: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    guest = verify_guest_by_id(request, guest_id, request.session.get("hotel_id"), db)
    csrf_token = generate_csrf_token()
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
    if not validate_csrf_token(csrf_token):
        add_flash_message(request, "Token de segurança invéliado, operação finalizada.", "danger")
        return RedirectResponse(url="/auth", status_code=303)

    guest = verify_guest_by_id(request, guest_id, request.session.get("hotel_id"), db)
    guest_updater(request, guest, email, phone_number, db)

    if next:
        return RedirectResponse(url=next, status_code=303)
    return RedirectResponse(url="/dashboard_guests", status_code=303)

@router.get("/delete/{guest_id}/{guest_cpf}", response_class=HTMLResponse, include_in_schema=False)
def delete_guest(
    guest_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    guest = verify_guest_by_id(request, guest_id, request.session.get("hotel_id"), db)
    guest_delete(request, db, guest)
    return RedirectResponse(url="/dashboard_guests", status_code=303)
    

