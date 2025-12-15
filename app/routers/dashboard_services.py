from fastapi import APIRouter, Depends, Request, Query, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from utils.session_guard import require_session
from core.config import SessionLocal
from schemas.services import ServicesOut
from typing import List, Optional
from sqlalchemy.orm import Session
from models.services import Services
from models.reservations import Reservations
from models.rooms import Rooms
from utils.flash import render, add_flash_message

router = APIRouter(
    prefix='/dashboard_services',
    tags=['services'],
    dependencies=[Depends(require_session)]
)

api_router = APIRouter(
    prefix='/api',
    tags=['api_services']
)
templates = Jinja2Templates(directory='app/templates')

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@api_router.get('/get_services_requests', response_model=List[ServicesOut])
def get_services_requests(
    request: Request,
    reservation_id: Optional[int] = Query(None, description="Filtrar pelo ID da reserva"),
    guest_id: Optional[int] = Query(None, description="Filtrar pelo ID do hóspede"),
    room_id: Optional[int] = Query(None, description="Filtrar pelo ID do quarto"),
    status: Optional[str] = Query(None, description="Filtrar pelo status do pedido"),
    db: Session = Depends(get_db)
):
    if request.session.get("Hotel_id"):
        if request.session.get("Hotel_id") != hotel_id:
            return HTTPException(status_code=404, detail="Erro!")
    query = db.query(Services)

    if reservation_id:
        query = query.filter(Services.reservation_id == reservation_id)
    if guest_id:
        query = query.filter(Services.guest_id == guest_id)
    if room_id:
        query = query.filter(Services.room_id == room_id)
    if status:
        query = query.filter(Services.status.ilike(f'&{status}%'))

    requests = query.all()

    if not requests:
        raise HTTPException(status_code=404, detail="Nenhum pedido encontrado")
    
    return requests

@router.get('', response_class=HTMLResponse, include_in_schema=False)
def services_requests(
    request: Request,
    db: Session = Depends(get_db)
):
    hotel_id = request.session.get("hotel_id")

    reservations = db.query(Reservations).filter(
        Reservations.status == 'checked_in'
        ).join(Rooms, Rooms.id == Reservations.id)

    return render(
        templates,
        request,
        "dashboard/services/services.html",
        {
            
        }
    )