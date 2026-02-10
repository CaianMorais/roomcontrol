# import de libs padrao
import datetime
from typing import List, Optional

# import de libs da third-party
from fastapi import APIRouter, HTTPException, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import paginate as sa_paginate

# import de funções da aplicação local
from app.core.config import get_db
from app.core.security import generate_csrf_token, validate_csrf_token
from app.models.rooms import Rooms
from app.utils.flash import add_flash_message, render
from app.utils.session_guard import require_session
from app.schemas.reservations import ReservationOut
from app.models.reservations import Reservations
from app.models.guest import Guest
from app.models.hotel import Hotel
from app.helpers.paginate import paginate
from app.helpers.verify_guest import verify_guest_by_id, verify_guest_by_cpf
from app.helpers.verify_room import verify_room
from app.helpers.reservations.booked_checkin import booked_to_checkin
from app.helpers.reservations.checkin_to_checkout import checkin_to_checkout
from app.helpers.reservations.cancel_reservation import cancel_reservation
from app.helpers.reservations.price_calculator import calc_price
from app.helpers.reservations.fast_update_reservation import fast_update_reservation
from app.helpers.reservations.create_reservation import verify_and_create_reservation
from app.helpers.reservations.filter_reservations import filter_reservations
from app.helpers.reservations.order_reservations import order_reservations
from app.helpers.reservations.conflict_guest import conflict_guest
from app.helpers.reservations.guest_availability import guest_availability
from app.helpers.reservations.room_availability import room_availability
from app.core.dependencies import get_api_hotel

router = APIRouter(
    prefix="/dashboard_reservations",
    tags=["reservations"],
    dependencies=[Depends(require_session)]
)

api_router = APIRouter(
    prefix="/api",
    tags=["reservations"],
    dependencies=[Depends(get_api_hotel)]
)

templates = Jinja2Templates(directory="app/templates")

@api_router.get("/reservations", response_model=List[ReservationOut], summary="Filtrar reservas")
def get_reservations(
    hotel_id: int = Depends(get_api_hotel),
    hotel_name: Optional[str] = Query(None, description="Filtrar pelo nome do hotel"),
    guest_id: Optional[int] = Query(None, description="Filtrar pelo ID do hóspede"),
    guest_name: Optional[str] = Query(None, description="Filtrar pelo nome do hóspede"),
    room_number: Optional[str] = Query(None, description="Filtrar pelo número do quarto"),
    check_in: Optional[str] = Query(None, description="Filtrar pela data de check-in"),
    check_out: Optional[str] = Query(None, description="Filtrar pela data de check-out"),
    db: Session = Depends(get_db)
):
    query = (
        db.query(Reservations)
        .options(
            joinedload(Reservations.guest),
            joinedload(Reservations.room).joinedload(Rooms.hotel),
        )
    )
    query = query.join(Rooms, Reservations.room_id == Rooms.id).join(Hotel, Rooms.hotel_id == Hotel.id).filter(Hotel.id == hotel_id)

    if hotel_name:
        query = query.join(Rooms, Reservations.room_id == Rooms.id).join(Hotel, Rooms.hotel_id == Hotel.id).filter(Hotel.name.ilike(f"%{hotel_name}%"))
    if guest_id:
        query = query.filter(Reservations.guest_id == guest_id)
    if guest_name:
        query = query.join(Guest, Guest.id == Reservations.guest_id) \
            .filter(Guest.name.ilike(f"%{guest_name}%"))
    if room_number:
        query = query.join(Rooms, Reservations.room_id == Rooms.id).filter(Rooms.room_number == room_number)
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
    check_out: Optional[str] = Query(None, description="Data do check-out"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=200),
):
    hotel_id = request.session.get("hotel_id")
    has_filter = False

    query = db.query(Reservations, Rooms.room_number, Guest.name, Guest.id) \
        .join(Rooms, Rooms.id == Reservations.room_id) \
        .join(Guest, Guest.id == Reservations.guest_id) \
        .filter(Rooms.hotel_id == hotel_id) \

    if (search or room or status or (interval_in and check_in) or (interval_out and check_out)):
        has_filter = True
        query = filter_reservations(request, has_filter, query, search, room, status, interval_in, check_in, interval_out, check_out)

    query = order_reservations(query)

    params = Params(page=page, size=per_page)
    page_obj = sa_paginate(db, query, params)

             
    return render(
        templates,
        request,
        "dashboard/reservations/reservations.html",
        {
            "request": request,
            "reservations": page_obj.items,
            "hotel_id": hotel_id,
            "has_filter": has_filter,
            "pager": {
                "page": page_obj.page,
                "pages": page_obj.pages,
                "per_page": page_obj.size,
                "total": page_obj.total,
            },
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
        guest = verify_guest_by_id(request, guest_id, hotel_id, db)
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
    guest_conflict = None

    # se tiver hospede específicado
    if guest_id:
        guest_conflict = conflict_guest(guest_id, check_in, check_out, db)
        available_guests = []
    else:
        available_guests = guest_availability(hotel_id, check_in, check_out, db)
    
    # Quartos disponíveis
    available_rooms = room_availability(db, check_in, check_out, hotel_id)

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
    cpf: str = Form(...),
    room_id: int = Form(...),
    check_in: datetime.datetime = Form(...),
    check_out: datetime.datetime = Form(...),
    check_in_now: bool = Form(False),
    csrf_token: str = Form(...)
):
    if not validate_csrf_token(csrf_token):
        add_flash_message(request, "Token de segurança inválido", "danger")
        return RedirectResponse(url="/dashboard_reservations/new", status_code=303)

    hotel_id = request.session.get("hotel_id")
    
    guest = verify_guest_by_cpf(request, cpf.replace(".", "").replace("-", ""), hotel_id, db)
    room = verify_room(request, room_id, hotel_id, db)

    reservation = verify_and_create_reservation(request, check_in, check_out, check_in_now, room, guest, db)

    add_flash_message(request, "Reserva criada com sucesso!", "success")
    return RedirectResponse(url=f"/dashboard_reservations/manage/{reservation.id}", status_code=303)

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
    verify_room(request, room.id, hotel_id, db)
    
    guest = db.query(Guest).filter(Guest.id == reservation.guest_id) \
    .filter(Guest.hotel_id == hotel_id) \
    .first()
    
    success, msg = fast_update_reservation(reservation, room, db)

    if not success:
        return JSONResponse(
            status_code=400,
            content={
                "message": msg,
            },
        )
    # Só leva reservation.status pro front se for sucesso (é como o js sabe que deu certo)
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
    
    booked_to_checkin(request, check_in, reservation, db)
    checkin_to_checkout(request, check_out, reservation, db)
    cancel_reservation(request, cancel, reservation, db)
    price = calc_price(reservation)

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

@router.get('/update_request_auth/{reservation_id}', include_in_schema=False)
def update_request_auth(
    request: Request,
    reservation_id: int,
    db: Session = Depends(get_db)
):
    
    reservation = db.query(Reservations).filter(Reservations.id == reservation_id).first()

    if reservation.allow_request_services:
        reservation.allow_request_services = False
        db.commit()
        db.refresh(reservation)
        return JSONResponse({
            "ok": True,
            "message": "O hóspede não está mais autorizado a solicitar serviços para essa reserva"
        })
    else:
        reservation.allow_request_services = True
        db.commit()
        db.refresh(reservation)
        return JSONResponse({
            "ok": True,
            "message": "O hóspede está autorizado a solicitar serviços para essa reserva"
        })