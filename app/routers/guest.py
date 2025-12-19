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

    return render(
        templates,
        request,
        'auth/guest_access.html',
        {
            'csrf_token': csrf_token
        }
    )

@router.post('/access', response_class=HTMLResponse, include_in_schema=False)
def guest_access(
    request: Request,
    csrf_token: str = Form(...),
    cpf: str = Form(...),
    db: Session = Depends(get_db)
):
    if not validate_csrf_token(csrf_token):
        add_flash_message(request, "Token de segurança invéliado, operação finalizada.", "danger")
        return RedirectResponse(url="/guests", status_code=303)

    guest = db.query(Guest) \
    .filter_by(cpf=cpf) \
    .first()

    reserva = db.query(Reservations) \
    .filter(Reservations.guest_id == guest.id) \
    .order_by(desc(Reservations.created_at)) \
    .first()
    
    return reserva.id