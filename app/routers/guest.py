from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query, Request, Form, Depends, APIRouter
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import desc
from sqlalchemy.orm import Session
from validate_docbr import CPF
from fastapi.templating import Jinja2Templates

from core.config import SessionLocal
from schemas.guest import GuestCreate, GuestOut
from models.guest import Guest
from models.rooms import Rooms
from models.reservations import Reservations
from core.security import validate_csrf_token, generate_csrf_token
from utils.flash import render, add_flash_message

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(prefix="/guests", tags=["guests"])
api_router = APIRouter(prefix="/api", tags=["api_guests"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get('', response_class=HTMLResponse, include_in_schema=False)
def guest(
    request: Request,
):
    csrf_token = generate_csrf_token()
    request.session['csrf_token'] = csrf_token
    return render(
        templates,
        request,
        'auth/guest_access.html',
        {
            'csrf_token': csrf_token
        }
    )

@router.get('/access', response_class=HTMLResponse, include_in_schema=False)
def guest_access(
    request: Request,
    token: Optional[str] = Query(None),
    cpf: Optional[str] = Query(None),
    res: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):

    if not token or token != request.session.get('csrf_token') or not validate_csrf_token(token):
        add_flash_message(request, 'Token inválido. Por favor, tente novamente.', 'danger')
        return RedirectResponse(request.url_for('guest'), status_code=303)
    
    guest = db.query(Guest) \
    .filter(Guest.cpf == cpf) \
    .first()

    if not guest:
        add_flash_message(request, 'CPF não encontrado. Verifique e tente novamente.', 'danger')
        return RedirectResponse(request.url_for('guest'), status_code=303)

    reserva = db.query(Reservations, Rooms) \
    .join(Rooms, Reservations.room_id == Rooms.id) \
    .filter(Reservations.id == res) \
    .order_by(desc(Reservations.created_at)) \
    .first()

    if not reserva or reserva.Reservations.guest_id != guest.id:
        add_flash_message(request, 'Reserva não encontrada. Verifique e tente novamente.', 'danger')
        return RedirectResponse(request.url_for('guest'), status_code=303)
    
    request.session["reservation_id"] = reserva.Reservations.id

    return render(
        templates,
        request,
        'guests_access/reservation.html',
        {
            'guest': guest,
            'reserva': reserva
        }
    )

@router.post('/request', response_class=HTMLResponse, include_in_schema=False)
def request_service(
    request: Request,
    service_description: str = Form(...),
    db: Session = Depends(get_db)
):
    reservation_id = request.session.get("reservation_id")
    if not reservation_id:
        add_flash_message(request, 'Reserva não encontrada na sessão. Por favor, faça login novamente.', 'danger')
        return RedirectResponse(request.url_for('guest'), status_code=303)
    
    reserva = db.query(Reservations).filter(Reservations.id == reservation_id).first()
    if not reserva:
        add_flash_message(request, 'Reserva não encontrada. Verifique e tente novamente.', 'danger')
        return RedirectResponse(request.url_for('guest'), status_code=303)