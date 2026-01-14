from fastapi import APIRouter, Body, Depends, Request, Query, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from utils.session_guard import require_session
from core.config import SessionLocal
from schemas.services import ServicesOut
from schemas.table_services import TableServicesOut
from typing import List, Optional, Literal
from sqlalchemy.orm import Session, joinedload
from models.services import Services
from models.reservations import Reservations
from models.rooms import Rooms
from models.guest import Guest
from models.hotel import Hotel
from utils.flash import render, add_flash_message
from helpers.services.query_requests import query_requests
from helpers.services.update_request_status import update_req_status

router = APIRouter(
    prefix='/dashboard_services',
    tags=['services'],
    dependencies=[Depends(require_session)]
)

api_router = APIRouter(
    prefix='/api',
    tags=['services']
)
templates = Jinja2Templates(directory='app/templates')

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

###################### API START ######################
@api_router.get('/services_requests', response_model=List[ServicesOut], summary="Filtrar pedidos de serviços")
def get_services_requests(
    request: Request,
    reservation_id: Optional[int] = Query(None, description="Filtrar pelo número da reserva"),
    guest_cpf: Optional[int] = Query(None, description="Filtrar pelo CPF do hóspede"),
    guest_name: Optional[str] = Query(None, description="Filtrar pelo nome do hóspede"),
    room_number: Optional[str] = Query(None, description="Filtrar pelo número do quarto"),
    hotel_id: Optional[int] = Query(None, description="Filtrar pelo ID do hotel"),
    hotel_name: Optional[str] = Query(None, description="Filtrar pelo nome do hotel"),
    status: Optional[Literal['pending', 'in_progress', 'completed']] = Query(None, description="Filtrar pelo status do pedido"),
    db: Session = Depends(get_db)
):
    query = (
        db.query(Services)
        .options(
            joinedload(Services.reservation).joinedload(Reservations.guest),
            joinedload(Services.reservation).joinedload(Reservations.room).joinedload(Rooms.hotel)
        )
    )

    if reservation_id:
        query = query.filter(Services.reservation_id == reservation_id)
    if guest_cpf:
        query = query.join(Guest, Services.guest_id == Guest.id).filter(Guest.cpf == guest_cpf)
    if guest_name:
        query = query.join(Guest, Services.guest_id == Guest.id).filter(Guest.name.ilike(f'%{guest_name}%'))
    if room_number:
        query = query.join(Rooms, Services.room_id == Rooms.id).filter(Rooms.room_number == room_number)
    if hotel_id:
        query = query.join(Rooms, Services.room_id == Rooms.id).join(
            Hotel, Rooms.hotel_id == Hotel.id
        ).filter(Hotel.id == hotel_id)
    if hotel_name:
        query = query.join(Rooms, Services.room_id == Rooms.id).join(
            Hotel, Rooms.hotel_id == Hotel.id
        ).filter(Hotel.name.ilike(f'%{hotel_name}%'))
    if status:
        query = query.filter(Services.status.ilike(f'%{status}%'))


    requests = query.all()

    if not requests:
        raise HTTPException(status_code=404, detail="Nenhum pedido encontrado")
    
    return requests

@api_router.get('/table_services_requests', response_model=List[TableServicesOut], summary="Filtrar dados para a tabela de pedidos de serviço na view")
def get_table_services_requests(
    request: Request,
    hotel_id: int,
    db: Session = Depends(get_db)
):
    query = (
        db.query(Services)
        .options(
            joinedload(Services.reservation).joinedload(Reservations.guest),
            joinedload(Services.reservation).joinedload(Reservations.room).joinedload(Rooms.hotel)
        )
    )

    if hotel_id == request.session.get("hotel_id"):
        query = query.join(Rooms, Services.room_id == Rooms.id).join(
            Hotel, Rooms.hotel_id == Hotel.id
        ).filter(Hotel.id == hotel_id)

    requests = query.all()

    if not requests:
        return []
    
    return requests

###################### API END ######################

@router.get('', response_class=HTMLResponse, include_in_schema=False)
def services_requests(
    request: Request,
    db: Session = Depends(get_db)
):
    hotel_id = request.session.get("hotel_id")

    return render(
        templates,
        request,
        "dashboard/services/services.html",
        {
            "hotel_id": hotel_id
        }
    )

@router.get('/pedido/{request_id}', response_class=HTMLResponse, include_in_schema=False)
def view_request(
    request: Request,
    request_id: int,
    db: Session = Depends(get_db)
):
    service_request = query_requests(request, db, request.session.get('hotel_id'), request_id)
    
    # seta o id do serviço na sessão para fazer update sem precisar passar o id pelo template
    request.session['service_id'] = service_request.Services.id

    return render(
        templates,
        request,
        "dashboard/services/view_request.html",
        {
            "service": service_request,
        }
    )
    
@router.post('/update_status', include_in_schema=False)
def update_service_status(
    request: Request,
    payload: dict = Body(...),
    db: Session = Depends(get_db)
):
    new_status = payload.get("status")
    response = update_req_status(request, db, payload, new_status)
    
    return response