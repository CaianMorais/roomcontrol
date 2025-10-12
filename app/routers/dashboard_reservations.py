from decimal import Decimal
import sys
import datetime
from app.core.config import SessionLocal
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Form, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import case, or_
from sqlalchemy.orm import Session
from passlib.hash import bcrypt
from math import ceil

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
def reservations(
    request: Request,
    db: Session = Depends(get_db),
    search: Optional[str] = Query("", description="Reserva ou Hóspede"),
    room: Optional[str] = Query(None, description="ID do quarto"),
    status: Optional[str] = Query("", description="Situação da reserva"),
    interval_in: Optional[str] = Query("", description="Intervalo do check-in"),
    check_in: Optional[str] = Query(None, description="Data do check-in"),
    interval_out: Optional[str] = Query("", description="Intervalo do check-out"),
    check_out: Optional[str] = Query(None, description="Data do check-out")
):

    hotel_id = request.session.get("hotel_id")
    if not hotel_id:
        add_flash_message(request, "Hotel não selecionado.", "danger")
        return RedirectResponse(url="/dashboard", status_code=303)
    
    query = db.query(Reservations, Rooms.room_number, Guest.name, Guest.id) \
        .join(Rooms, Rooms.id == Reservations.room_id) \
        .join(Guest, Guest.id == Reservations.guest_id) \
        .filter(Rooms.hotel_id == hotel_id) \
        
    if search:
        query = query.filter(
            or_(
                Reservations.id == search,
                Guest.name.ilike(f"%{search}%")
            )
        )
    if room:
        query = query.filter(Rooms.id == room)
    if status:
        query = query.filter(Reservations.status == status)
    if interval_in and check_in:
        try:
            check_in_dt = datetime.datetime.strptime(check_in, '%Y-%m-%dT%H:%M')
            if interval_in == 'before':
                query = query.filter(Reservations.check_in < check_in_dt)
            elif interval_in == 'after':
                query = query.filter(Reservations.check_in > check_in_dt)
        except ValueError as e:
            add_flash_message(request, f"Erro: {e}", "danger")
    if interval_out and check_out:
        try:
            check_out_dt = datetime.datetime.strptime(check_out, "%Y-%m-%dT%H:%M")
            if interval_out == 'before':
                query = query.filter(Reservations.check_out < check_out_dt)
            elif interval_out == 'after':
                query = query.filter(Reservations.check_out > check_out_dt)
        except ValueError as e:
            add_flash_message(request, f"Erro: {e}", "danger")
            
    reservations = query.order_by(
        case(
            (Reservations.status == "booked", 1),
            (Reservations.status == "checked_in", 2),
            (Reservations.status == "checked_out", 3),
            (Reservations.status == "canceled", 4),
        ),
        Reservations.check_in
    ).all()
    
    if search or room or status or (interval_in and check_in) or (interval_out and check_out):
        if len(reservations) == 0:
            add_flash_message(request, 'Nenhuma reserva encontrada com os filtros aplicados.', "warning")
            return RedirectResponse(url='/dashboard_reservations', status_code=303)
        elif len(reservations and (room or status or (interval_in and check_in) or (interval_out and check_out))) > 0:
            add_flash_message(request, "Filtro aplicado", "success")
             
    return render(
        templates,
        request,
        "dashboard/reservations/reservations.html",
        {
            "request": request,
            "reservations": reservations,
            "hotel_id": hotel_id,
            "has_filter": True if (search or room or status or (interval_in and check_in) or (interval_out and check_out)) else False
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

@router.get("/check_availability", include_in_schema=False)
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
            Reservations.check_out > check_in,
            Reservations.status.in_(["booked", "checked_in"])
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
        Rooms.status != "maintenance",
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
    name: Optional[str] = Query(""),
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
    
    if check_out < datetime.datetime.now():
        add_flash_message(request, "O horário de check-out não pode ser menor que o horário atual.", "danger")
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

## DESENVOLVER ROTAS QUE ALTERAM A SITUAÇÃO DA RESERVA DINAMICAMENTE (JS)

@router.post("/update/{reservation_id}", include_in_schema=False)
def update_reservation(
    request: Request,
    reservation_id: int,
    db: Session = Depends(get_db),
):
    
    hotel_id = request.session.get('hotel_id')
    reservation = db.query(Reservations).filter(Reservations.id == reservation_id).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Reserva não encontrada")
    
    room = db.query(Rooms).filter(Rooms.id == reservation.room_id).first()
    if not room or room.hotel_id != hotel_id:
        raise HTTPException(status_code=404, detail="Quarto não encontrado")
    
    guest = db.query(Guest).filter(Guest.id == reservation.guest_id) \
    .filter(Guest.hotel_id == hotel_id) \
    .first()
    
    # Agendada -> Check-in
    if reservation.status == 'booked' and room.status == 'available':
        reservation.status = 'checked_in'
        reservation.check_in = datetime.datetime.now()
        room.status = 'occupied'
    # Check-in -> Check-out
    elif reservation.status == 'checked_in' and room.status == 'occupied':
        reservation.status = 'checked_out'
        reservation.check_out = datetime.datetime.now()
        room.status = 'available'
    else:
        return {
            "message": f"Não foi possível modificar essa reserva."
        }

    db.commit()
    db.refresh(reservation)
    db.refresh(room)
    
    return {
        "id": reservation.id,
        "status": reservation.status,
        "guest" : guest.id if guest else None,
        "message": f"Reserva {reservation.id} atualizada."
    }

@router.get('/manage/{reservation_id}', include_in_schema=False)
def manage_reservation(
    request: Request,
    reservation_id: int,
    check_in: Optional[bool] = Query(False),
    check_out: Optional[bool] = Query(False),
    cancel: Optional[bool] = Query(False),
    db: Session = Depends(get_db)
):
    hotel_id = request.session.get('hotel_id')

    reservation = db.query(Reservations, Rooms.room_number, Guest, Rooms) \
        .join(Rooms, Rooms.id == Reservations.room_id) \
        .join(Guest, Guest.id == Reservations.guest_id) \
        .filter(Reservations.id == reservation_id) \
        .filter(Rooms.hotel_id == hotel_id) \
        .first()
    
    if not reservation:
        add_flash_message(request, "Reserva não encontrada", "warning")
        return RedirectResponse(url='/dashboard_reservations', status_code=303)
    
    days = reservation.Reservations.check_out - reservation.Reservations.check_in
    total_days = ceil(days.total_seconds() / (24 * 3600))
    price = reservation.Rooms.price * total_days
    
    if check_in and reservation.Reservations.status != 'checked_in':
        reservation.Reservations.status = 'checked_in'
        reservation.Reservations.check_in = datetime.datetime.now()
        reservation.Rooms.status = 'occupied'
        db.commit()
        db.refresh(reservation.Reservations)
        db.refresh(reservation.Rooms)
        add_flash_message(request, "Reserva atualizada com sucesso!", 'success')

    if check_out and reservation.Reservations.status != 'checked_out':
        reservation.Reservations.status = 'checked_out'
        reservation.Reservations.check_out = datetime.datetime.now()
        reservation.Rooms.status = 'available'
        db.commit()
        db.refresh(reservation.Reservations)
        db.refresh(reservation.Rooms)
        add_flash_message(request, "Reserva atualizada com sucesso!", 'success')

    if cancel and reservation.Reservations.status == 'canceled':
        add_flash_message(request, "A reserva já está cancelada", 'warning')
    elif cancel and reservation.Reservations.status == 'checked_out':
        add_flash_message(request, "A reserva já foi encerrada", 'warning')
    elif cancel and (reservation.Reservations.status == 'booked' or reservation.Reservations.status == 'checked_in'):
        reservation.Reservations.status = 'canceled'
        reservation.Rooms.status = 'available'
        db.commit()
        db.refresh(reservation.Reservations)
        db.refresh(reservation.Rooms)
        add_flash_message(request, "A reserva foi cancelada com sucesso", 'success')

        
    return render(
        templates,
        request,
        "dashboard/reservations/manage_reservation.html",
        {
            "request": request,
            "reservation": reservation,
            "price": price,
        }
    )