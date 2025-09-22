from decimal import Decimal
from app.core.config import SessionLocal
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Form, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from passlib.hash import bcrypt

from app.core.security import generate_csrf_token, validate_csrf_token
from app.models.rooms import Rooms
from app.utils.flash import add_flash_message, render
from app.utils.session_guard import require_session
from app.schemas.guest import GuestOut, GuestCreate, GuestBase
from app.models.guest import Guest

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

    return guests

@router.get("/new", response_class=HTMLResponse, include_in_schema=False)
def new_guest(request: Request, db: Session = Depends(get_db)):
    csrf_token = generate_csrf_token()
    hotel_id = request.session.get("hotel_id")
    rooms = db.query(Rooms).filter(Rooms.hotel_id == hotel_id).filter(Rooms.status == 'available').all()
    return render(
        templates,
        request,
        "dashboard/guests/new_guest.html",
        {
            "request": request,
            "csrf_token": csrf_token,
            "rooms": rooms
        }
    )
