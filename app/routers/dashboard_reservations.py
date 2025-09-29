from decimal import Decimal
import sys
import datetime
from app.core.config import SessionLocal
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Form, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session
from passlib.hash import bcrypt

from app.core.security import generate_csrf_token, validate_csrf_token
from app.models.rooms import Rooms
from app.utils.flash import add_flash_message, render
from app.utils.session_guard import require_session
from app.schemas.reservations import ReservationBase, ReservationCreate, ReservationOut
from app.models.reservations import Reservations
from app.models.guest import Guest

router = APIRouter(
    prefix="/dashboard_reservations",
    tags=["reservations"],
    dependencies=[Depends(require_session)]
)

api_router = APIRouter(prefix="/api", tags=["api_reservations"])
templates = Jinja2Templates(directory="app/templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@api_router.get("/get_reservations", response_model=List[ReservationOut])
def get_reservations(
    guest_id: Optional[int] = Query(None, description="Filtrar pelo ID do hóspede"),
    room_id: Optional[int] = Query(None, description="Filtrar pelo ID do quarto"),
    check_in: Optional[str] = Query(None, description="Filtrar pela data de check-in"),
    check_out: Optional[str] = Query(None, description="Filtrar pela data de check-out"),
    db: Session = Depends(get_db)
):
    query = db.query(Reservations)

    if guest_id:
        query = query.filter(Reservations.guest_id == guest_id)
    if room_id:
        query = query.filter(Reservations.room_id == room_id)
    if check_in:
        query = query.filter(Reservations.check_in == check_in)
    if check_out:
        query = query.filter(Reservations.check_out == check_out)

    reservations = query.all()

    if not reservations:
        raise HTTPException(status_code=404, detail="Nenhuma reserva encontrada")

    return reservations

@router.get("", response_class=HTMLResponse, include_in_schema=False)
def reservations(request: Request, db: Session = Depends(get_db)):


    ###### DESENVOLVER A FILTRAGEM DAS RESERVAS


    hotel_id = request.session.get("hotel_id")
    if not hotel_id:
        add_flash_message(request, "Hotel não selecionado.", "danger")
        return RedirectResponse(url="/dashboard", status_code=303)
    
    reservations = db.query(Reservations, Rooms.room_number, Guest.name) \
        .join(Rooms, Rooms.id == Reservations.room_id) \
        .join(Guest, Guest.id == Reservations.guest_id) \
        .filter(Rooms.hotel_id == hotel_id) \
        .all()
    
    return render(
        templates,
        request,
        "dashboard/reservations/reservations.html",
        {
            "request": request,
            "reservations": reservations
        }
    )

@router.get("/new", response_class=HTMLResponse, include_in_schema=False)
def new_reservation(
    request: Request,
    db: Session = Depends(get_db),
    guest_id: Optional[int] = Query(None, description="ID do hóspede para pré-seleção")
):
    hotel_id = request.session.get("hotel_id")
    if not hotel_id:
        add_flash_message(request, "Hotel não selecionado.", "danger")
        return RedirectResponse(url="/dashboard", status_code=303)
    
    if guest_id:
        guest = db.query(Guest).filter(Guest.hotel_id == hotel_id).filter(Guest.id == guest_id).first()
        if not guest:
            add_flash_message(request, "Esse hóspede não existe em seu hotel", "danger")
            return RedirectResponse(url="/dashboard_reservations", status_code=303)
    else:
        guest = []

    rooms = []

    csrf_token = generate_csrf_token()
    print(datetime.datetime.now())
    return render(
        templates,
        request,
        "dashboard/reservations/new_reservation.html",
        {
            "request": request,
            "guest": guest,
            "csrf_token": csrf_token,
            "rooms": rooms
        }
    )

@router.get("/check_availability")
def check_availability(
    request: Request,
    db: Session = Depends(get_db),
    check_in: datetime.datetime = Query(...),
    check_out: datetime.datetime = Query(...),
    guest_id: Optional[int] = Query(None),
):
    hotel_id = request.session.get("hotel_id")

    # Hóspede específico
    guest_conflict = None
    if guest_id:
        guest_conflict = db.query(Reservations).filter(
            Reservations.guest_id == guest_id,
            Reservations.check_in < check_out,
            Reservations.check_out > check_in
        ).first()
        print(bool(guest_conflict))
        available_guests = []
    else:
        # Hóspedes disponíveis
        reserved_guest_ids = db.query(Reservations.guest_id).filter(
            Reservations.check_in < check_out,
            Reservations.check_out > check_in
        ).subquery()

        available_guests = db.query(Guest).filter(
            Guest.hotel_id == hotel_id,
            ~Guest.id.in_(reserved_guest_ids)
        ).all()

    # Quartos disponíveis
    reserved_room_ids = db.query(Reservations.room_id).filter(
        Reservations.status.in_(["booked", "checked_in"]),
        Reservations.check_in < check_out,
        Reservations.check_out > check_in
    ).subquery()

    available_rooms = db.query(Rooms).filter(
        Rooms.hotel_id == hotel_id,
        Rooms.status == "available",
        ~Rooms.id.in_(reserved_room_ids)
    ).all()

    return {
        "guest_conflict": bool(guest_conflict),
        "available_guests": [
            {
                "id": g.id,
                "name": g.name,
                "cpf": g.cpf,
                "email": g.email,
                "phone_number": g.phone_number
            } for g in available_guests
        ],
        "available_rooms": [
            {
                "id": r.id,
                "room_number": r.room_number,
                "type": r.type,
                "capacity_adults": r.capacity_adults,
                "capacity_children": r.capacity_children,
                "price": r.price
            } for r in available_rooms
        ]
    }

@router.post("/create", response_class=HTMLResponse, include_in_schema=False)
def create_reservation(
    request: Request,
    db: Session = Depends(get_db),
    name: str = Form(...),
    cpf: str = Form(...),
    room_id: int = Form(...),
    check_in: datetime.datetime = Form(...),
    check_out: datetime.datetime = Form(...),
    csrf_token: str = Form(...)
):

    if not validate_csrf_token(csrf_token):
        add_flash_message(request, "Token de segurança inválido", "danger")
        return RedirectResponse(url="/dashboard_reservations/new", status_code=303)

    hotel_id = request.session.get("hotel_id")

    guest = db.query(Guest).filter(Guest.cpf == cpf).filter(Guest.hotel_id == hotel_id).first()
    room = db.query(Rooms).filter(Rooms.id == room_id).filter(Rooms.hotel_id == hotel_id).first()

    if not guest:
        add_flash_message(request, "Hóspede não encontrado.", "danger")
        return RedirectResponse(url="/dashboard_reservations/new", status_code=303)

    if not room:
        add_flash_message(request, "Quarto não encontrado ou indisponível.", "danger")
        return RedirectResponse(url="/dashboard_reservations/new", status_code=303)
    
    if check_out <= check_in:
        add_flash_message(request, "Data de check-out deve ser posterior à data de check-in.", "danger")
        return RedirectResponse(url="/dashboard_reservations/new", status_code=303)
    
    if check_in > datetime.datetime.now():
        status= 'booked'
    elif check_in <= datetime.datetime.now():
        status= 'checked_in'
        room.status = 'occupied'
    else:
        add_flash_message(request, "Data de check-in inválida.", "danger")
        return RedirectResponse(url="/dashboard_reservations/new", status_code=303)

    new_reservation = Reservations(
        guest_id=guest.id,
        room_id=room_id,
        check_in=check_in,
        check_out=check_out,
        status=status
    )

    db.add(new_reservation)
    db.commit()

    add_flash_message(request, "Reserva criada com sucesso!", "success")
    return RedirectResponse(url="/dashboard_reservations", status_code=303)
