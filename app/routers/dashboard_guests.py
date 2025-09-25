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
    
    # for g in guests:
    #     if g.email == "":
    #         g.email = None

    return guests


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def guests(request: Request, db: Session = Depends(get_db)):
    hotel_id = request.session.get("hotel_id")
    # guests = db.query(Guest, Reservations.check_in, Rooms.room_number) \
    #     .join(Reservations, Reservations.guest_id == Guest.id) \
    #     .join(Rooms, Rooms.hotel_id == hotel_id) \
    #     .filter(Guest.hotel_id == hotel_id) \
    #     .all()
    ReservationAlias = aliased(Reservations)
    RoomAlias = aliased(Rooms)

    guests = (
        db.query(
            Guest,
            ReservationAlias.check_in,
            RoomAlias.room_number
        )
        .outerjoin(
            ReservationAlias, ReservationAlias.guest_id == Guest.id
        )
        .outerjoin(
            RoomAlias, RoomAlias.id == ReservationAlias.room_id
        )
        .filter(Guest.hotel_id == hotel_id)
        .all()
    )
    return render(
        templates,
        request,
        "dashboard/guests/guests.html",
        {
            "request": request,
            "guests": guests
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

    if db.query(Guest).filter(Guest.cpf == cpf).filter(Guest.hotel_id == hotel_id).first():
        add_flash_message(request, "CPF já cadastrado no seu hotel", "danger")
        return RedirectResponse(url="/dashboard_guests/new", status_code=status.HTTP_303_SEE_OTHER)
    
    new_guest = Guest(
        name=name,
        cpf=cpf,
        email=email,
        phone_number=phone_number,
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

@router.get('/edit/{guest_id}', response_class=HTMLResponse, include_in_schema=False)
def edit_guest(guest_id: int, request: Request, db: Session = Depends(get_db)):
    guest = db.query(Guest).filter_by(id=guest_id, hotel_id=request.session.get("hotel_id")).first()
    if guest.hotel_id != request.session.get("hotel_id"):
        add_flash_message(request, "Hóspede não encontrado.", "warning")
        return RedirectResponse(url="/dashboard_guests", status_code=303)
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
            "csrf_token": csrf_token
        }
    )

@router.post('/edit/{guest_id}', response_class=HTMLResponse, include_in_schema=False)
def update_guest(
    request: Request,
    guest_id: int,
    email: str = Form(...),
    phone_number: str = Form(...),
    csrf_token: str = Form(...),
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
    return RedirectResponse(url="/dashboard_guests", status_code=303)

## criar rota de deletar hospede (verificando se tem reserva ativa ou agendada)