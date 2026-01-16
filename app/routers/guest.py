from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query, Request, Form, Depends, APIRouter
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy import desc
from sqlalchemy.orm import Session
from validate_docbr import CPF
from fastapi.templating import Jinja2Templates

from models.services import Services
from core.config import SessionLocal
from schemas.guest import GuestCreate, GuestOut
from models.guest import Guest
from models.rooms import Rooms
from models.reservations import Reservations
from core.security import validate_csrf_token, generate_csrf_token
from utils.flash import render, add_flash_message
from helpers.guest_access.access import find_guest, find_reservation, find_services
from helpers.guest_access.request_service import create_request_service

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
        return RedirectResponse(request.url_for('guest'), status_code=303)
    
    guest = find_guest(request, db, cpf)
    reservation = find_reservation(request, db, res, guest)
    request.session["reservation_id"] = reservation.Reservations.id
    services = find_services(db, reservation)

    return render(
        templates,
        request,
        'guests_access/reservation.html',
        {
            'guest': guest,
            'reserva': reservation,
            'services': services
        }
    )

@router.post('/request', include_in_schema=False)
def request_service(
    request: Request,
    service_description: str = Form(...),
    db: Session = Depends(get_db)
):
    reservation_id = request.session.get("reservation_id")
    if not reservation_id:
        add_flash_message(request, 'Reserva não encontrada na sessão. Por favor, faça login novamente.', 'danger')
        return RedirectResponse(request.url_for('guest'), status_code=303)
    
    new_request = create_request_service(request, db, reservation_id, service_description)

    if new_request:
        return JSONResponse({
            "ok": True,
            "message": "Solicitação de serviço recebida com sucesso.",
            "service_description": service_description
        })
    else:
        return JSONResponse({
            "ok": False,
            "message": "Algo deu errado com sua solicitação",
            "service_description": service_description
        })

@router.get('/load_request/{request_id}', include_in_schema=False)
def load_service_request(
    request: Request,
    request_id: int,
    db: Session = Depends(get_db)
):
    service_request = db.query(Services).filter(Services.id == request_id).first()
    if not service_request:
        return JSONResponse({
            "ok": False,
            "message": "Solicitação de serviço não encontrada."
        })
    
    return JSONResponse({
        "ok": True,
        "service_request": {
            "id": service_request.id,
            "request": service_request.request,
        }
    })