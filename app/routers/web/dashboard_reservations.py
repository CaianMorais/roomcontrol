# import de libs padrao
import datetime
from typing import Optional

# import de libs da third-party
from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import paginate as sa_paginate

# import de funções da aplicação local
from app.core.config import get_db
from app.core.security import generate_csrf_token, validate_csrf_token
from app.utils.flash import add_flash_message, render
from app.utils.session_guard import require_session
from app.services.audit_service import AuditService
from app.services.reservation_service import ReservationService
from app.services.guest_service import GuestService
from app.services.room_service import RoomsService

# confiraução do router e template
router = APIRouter(
    prefix="/dashboard_reservations",
    tags=["reservations"],
    dependencies=[Depends(require_session)]
)
templates = Jinja2Templates(directory="app/templates")


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
    # captura o hotel e inicia a query
    hotel_id = request.session.get("hotel_id")
    has_filter = False

    query = ReservationService.list_reservations(db, hotel_id)

    # se tiver algum dos filtros, joga pra helper que faz os filtros
    if (search or room or status or (interval_in and check_in) or (interval_out and check_out)):
        has_filter = True
        query, error = ReservationService.filter_reservations(query, search, room, status, interval_in, check_in, interval_out, check_out)
        if error:
            add_flash_message(request, error, "danger")
            return RedirectResponse(url=request.url_for('reservations'), status_code=303)

    # joga no paginate
    params = Params(page=page, size=per_page)
    page_obj = sa_paginate(db, query, params)

    if not page_obj.items and has_filter:
        add_flash_message(request, 'Nenhuma reserva encontrada com os filtros aplicados.', "warning")
        return RedirectResponse(url=request.url_for('reservations'), status_code=303)


    # renderiza
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
    # captura o hotel
    hotel_id = request.session.get("hotel_id")
    
    # se tiver guest, já inicia o formulário com ele instanciadp
    if guest_id:
        guest = GuestService.get_guest(db, hotel_id, guest_id)
    else:
        guest = []

    # inicia uma lista de quartos vazia para buscar disponibilidade depois
    rooms = []

    csrf_token = generate_csrf_token(request)
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
    #captura o hotel
    hotel_id = request.session.get("hotel_id")
    # inicia a variavel de conflito do hospede
    guest_conflict = None

    # se tiver hospede específicado verifica se tem conflito de datas
    if guest_id:
        guest_conflict = ReservationService.guest_has_conflict(db, guest_id, check_in, check_out)
        available_guests = []
    # senão pega todos os hóspedes disponiveis na data desejada
    else:
        available_guests = ReservationService.get_available_guests(db, hotel_id, check_in, check_out)
    
    # envia as datas para a service verificar os quartos disponiveis na data desejada
    available_rooms = ReservationService.get_available_rooms(db, check_in, check_out, hotel_id)

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
    # captura hotel
    hotel_id = request.session.get("hotel_id")

    # valida token
    if not validate_csrf_token(request, csrf_token):
        add_flash_message(request, "Token de segurança inválido", "danger")
        return RedirectResponse(url=request.url_for('new_reservation'), status_code=303)
    
    # localiza hospede e quarto
    guest = GuestService.get_guest(db, hotel_id, cpf=cpf.replace(".", "").replace("-", ""))
    room = RoomsService.get_room(db, room_id, hotel_id)[0]

    # verifica datas (redundância) e cria a reserva
    reservation, error = ReservationService.create_reservation(db, check_in, check_out, check_in_now, room, guest)
    if error:
        add_flash_message(request, error, "danger")
        return RedirectResponse(url="/dashboard_reservations/new", status_code=303)

    # registra log
    AuditService.register(db, hotel_id, 'create', 'reservation', reservation.id, request.session.get("collaborator_id"))

    add_flash_message(request, "Reserva criada com sucesso!", "success")
    return RedirectResponse(url=request.url_for("manage_reservation", reservation_id=reservation.id), status_code=303)

@router.get('/manage/{reservation_id}', include_in_schema=False)
def manage_reservation(
    request: Request,
    reservation_id: int,
    check_in: Optional[bool] = Query(False),
    check_out: Optional[bool] = Query(False),
    cancel: Optional[bool] = Query(False),
    db: Session = Depends(get_db)
):
    # captura o hotel
    hotel_id = request.session.get('hotel_id')

    # localiza a reserva
    reservation, error = ReservationService.get_reservation(db, reservation_id, hotel_id)
    
    if error:
        add_flash_message(request, error, "warning")
        return RedirectResponse(url=request.url_for('reservations'), status_code=303)
    
    # service que atualiza a situação da reserva
    # baseado no parametro true trazido na URL
    if check_in or check_out or cancel:
        reservation, error = ReservationService.update_status_from_manage(db, check_in, check_out, cancel, reservation)
        if error:
            add_flash_message(request, error, "warning")
            return RedirectResponse(url=request.url_for('manage_reservation', reservation_id=reservation_id), status_code=303)
        else:
            AuditService.register(db, hotel_id, 'update', 'reservation', reservation.Reservations.id, request.session.get("collaborator_id"))
        

    # recalcula o preço das diárias
    price = ReservationService.get_reservation_price(reservation)

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

@router.post("/update/{reservation_id}", include_in_schema=False)
def update_reservation(
    request: Request,
    reservation_id: int,
    db: Session = Depends(get_db),
):
    # captura o hotel
    hotel_id = request.session.get('hotel_id')

    # localiza a reserva
    reservation, error = ReservationService.get_reservation(db, reservation_id, hotel_id)
    if error:
        return JSONResponse(
            status_code=404,
            content={"detail": error}
        )
    
    # localiza o quarto e verifica se ele pertence ao hotel
    room, error = RoomsService.get_room(db, reservation.Rooms.id, hotel_id)
    if error:
        return JSONResponse(
            status_code=404,
            content={"detail": error}
        )

    # localiza o hospede vinculado a reserva
    guest = GuestService.get_guest(db, hotel_id, reservation.Guest.id)
    if not guest:
        return JSONResponse(
            status_code=404,
            content={"detail": error}
        )
    
    # atualiza a reserva rapidamente pela tabela
    #reservation, error = fast_update_reservation(reservation.Reservations, room, db)
    reservation, error = ReservationService.update_status_from_table(db, reservation, room)

    if error:
        return {
            'message': error
        }
    # registra log
    AuditService.register(db, hotel_id, 'update', 'reservation', reservation.Reservations.id, request.session.get("collaborator_id"))

    # Só leva reservation.status pro front se for sucesso (é como o js sabe que deu certo)
    return {
        "id": reservation.Reservations.id,
        "status": reservation.Reservations.status,
        "guest" : guest.id if guest else None,
        "message": f"Reserva {reservation.Reservations.id} atualizada."
    }

@router.get('/update_request_auth/{reservation_id}', include_in_schema=False)
def update_request_auth(
    request: Request,
    reservation_id: int,
    db: Session = Depends(get_db)
):
    # captura o hotel e a reserva
    hotel_id = request.session.get("hotel_id")
    reservation, error = ReservationService.get_reservation(db, reservation_id, hotel_id)
    if error:
        add_flash_message(request, error, "warning")
        return RedirectResponse(url=request.url_for('reservations'), status_code=303)

    
    reservation, error, message = ReservationService.change_requests_services(db, reservation)
    if error:
        return JSONResponse({
            "ok": False,
            "message": error
        })

    AuditService.register(db, hotel_id, 'update', 'reservation', reservation.Reservations.id, request.session.get("collaborator_id"))
    return JSONResponse({
        "ok": True,
        "message": message
    })