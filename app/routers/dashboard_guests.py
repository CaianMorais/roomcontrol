import datetime
from decimal import Decimal
from app.core.config import SessionLocal
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Form, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import cast, DateTime, outerjoin
from sqlalchemy.orm import Session, aliased
from passlib.hash import bcrypt

from app.core.security import generate_csrf_token, validate_csrf_token
from app.models.rooms import Rooms
from app.utils.flash import add_flash_message, render
from app.utils.session_guard import require_session
from app.schemas.guest import GuestOut, GuestCreate, GuestBase
from app.models.guest import Guest
from app.models.reservations import Reservations

router = APIRouter(
    prefix="/dashboard_guests",
    tags=["guests"],
    dependencies=[Depends(require_session)]
)

api_router = APIRouter(prefix="/api", tags=["api_guests"])
templates = Jinja2Templates(directory="app/templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@api_router.get("/get_guests", response_model=List[GuestOut])
def get_guests(
    guest_cpf: Optional[str] = Query(None, description="Filtrar pelo CPF do hóspede"),
    guest_name: Optional[str] = Query(None, description="Filtrar pelo nome do hóspede"),
    hotel_id: Optional[str] = Query(None, description="Filtrar pelo ID do hotel"),
    db: Session = Depends(get_db)
):
    query = db.query(Guest)

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
    cpf: Optional[str] = Query("", description="CPF do hóspede")
    ):
    hotel_id = request.session.get("hotel_id")
    ReservationAlias = aliased(Reservations)
    RoomAlias = aliased(Rooms)

    guests = (
        db.query(
            Guest,
            ReservationAlias.check_in,
            ReservationAlias.status,
            ReservationAlias.id,
            RoomAlias.room_number
        )
        .outerjoin(
            ReservationAlias, ReservationAlias.guest_id == Guest.id
        )
        .outerjoin(
            RoomAlias, RoomAlias.id == ReservationAlias.room_id
        )
        .filter(
            Guest.hotel_id == hotel_id,
            Guest.is_deleted == False,)
        .order_by(Guest.name)
    )

    if name:
        guests = guests.filter(Guest.name.ilike(f"%{name}%"))
        add_flash_message(request, f"Filtro aplicado", "success")
    if cpf:
        guests = guests.filter(Guest.cpf.like(f"%{cpf}%"))
        add_flash_message(request, f"Filtro aplicado", "success")

    return render(
        templates,
        request,
        "dashboard/guests/guests.html",
        {
            "request": request,
            "guests": guests.all(),
            "has_filter": True if (name or cpf) else False,
            "now": datetime.datetime.now()
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

    if db.query(Guest).filter(Guest.cpf == cpf).filter(Guest.hotel_id == hotel_id, Guest.is_deleted == False).first():
        add_flash_message(request, "CPF já cadastrado no seu hotel", "danger")
        return RedirectResponse(url="/dashboard_guests/new", status_code=status.HTTP_303_SEE_OTHER)
    elif db.query(Guest).filter(Guest.cpf == cpf).filter(Guest.hotel_id == hotel_id, Guest.is_deleted == True).first():
        guest = db.query(Guest).filter(Guest.cpf == cpf).filter(Guest.hotel_id == hotel_id, Guest.is_deleted == True).first()
        guest.name = name
        guest.email = email if email else None
        guest.phone_number = phone_number if phone_number else None
        guest.is_deleted = False

        db.commit()
        db.refresh(guest)
        add_flash_message(request, "Hóspede cadastrado com sucesso, continue com a reserva", "success")
        return RedirectResponse(
            url=f"/dashboard_reservations/new?guest_id={guest.id}",
            status_code=303,
        )
    else:
        new_guest = Guest(
            name=name,
            cpf=cpf,
            email=email if email else None,
            phone_number=phone_number if phone_number else None,
            hotel_id=hotel_id
        )
        db.add(new_guest)
        db.commit()
        db.refresh(new_guest)
        add_flash_message(request, "Hóspede cadastrado com sucesso, continue com a reserva", "success")
        return RedirectResponse(
            url=f"/dashboard_reservations/new?guest_id={new_guest.id}",
            status_code=303,
        )

@router.get('/edit/{guest_id}/{guest_cpf}', response_class=HTMLResponse, include_in_schema=False)
def edit_guest(
    guest_id: int,
    request: Request,
    next: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    guest = db.query(Guest).filter_by(id=guest_id, hotel_id=request.session.get("hotel_id"), is_deleted=False).first()
    if not guest:
        add_flash_message(request, "Hóspede não encontrado.", "warning")
        return RedirectResponse(url="/dashboard_guests", status_code=303)
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

    guest = db.query(Guest).filter_by(id=guest_id, hotel_id=request.session.get("hotel_id")).first()

    guest.email = email
    guest.phone_number = phone_number

    db.commit()
    db.refresh(guest)

    add_flash_message(request, f"Cadastro de {guest.name} editado com sucesso!", "success")
    print(next)
    if next:
        print(next)
        return RedirectResponse(url=next, status_code=303)
    return RedirectResponse(url="/dashboard_guests", status_code=303)

@router.get("/delete/{guest_id}/{guest_cpf}", response_class=HTMLResponse, include_in_schema=False)
def delete_guest(
    guest_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    hotel = request.session.get("hotel_id")
    guest = db.query(Guest).filter_by(id=guest_id, hotel_id=hotel).first()
    reservations = db.query(Reservations).filter_by(guest_id=guest.id).all()
    for res in reservations:
        if res.check_out > datetime.datetime.now():
            add_flash_message(request, "Esse hóspede tem uma reserva ativa ou agendada no momento, não é possível apaga-lo")
            return RedirectResponse(url="/dashboard_guests", status_code=303)
    
    guest.is_deleted = True
    db.commit()
    add_flash_message(request, f"O hóspede {guest.name} foi removido.")
    return RedirectResponse(url="/dashboard_guests", status_code=303)
    

