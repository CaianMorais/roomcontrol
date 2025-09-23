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
from app.models.reservations import Reservations

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


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def guests(request: Request, db: Session = Depends(get_db)):
    hotel_id = request.session.get("hotel_id")
    guests = db.query(Guest).filter(Guest.hotel_id == hotel_id).all()
    reservation = db.query(Reservations) #concluir consultas das reservas pra tabela de hospedes
    return render(
        templates,
        request,
        "dashboard/guests/guests.html",
        {
            "request": request,
            "guests": guests
        }
    )

@router.get("/new", response_class=HTMLResponse, include_in_schema=False)
def new_guest(request: Request, db: Session = Depends(get_db)):
    csrf_token = generate_csrf_token()
    return render(
        templates,
        request,
        "dashboard/guests/new_guest.html",
        {
            "request": request,
            "csrf_token": csrf_token,
        }
    )

@router.post("/create_guest", response_class=HTMLResponse, include_in_schema=False)
def create_guest(
    request: Request,
    db: Session = Depends(get_db),
    name: str = Form(...),
    cpf: str = Form(...),
    email: str = Form(...),
    phone_number: str = Form(...),
    csrf_token: str = Form(...)
):
    if not validate_csrf_token(csrf_token):
        add_flash_message(request, "Token de segurança inválido", "danger")
        return RedirectResponse(url="/dashboard_guests/new", status_code=status.HTTP_303_SEE_OTHER)

    hotel_id = request.session.get("hotel_id")

    if db.query(Guest).filter(Guest.cpf == cpf).filter(Guest.hotel_id == hotel_id).first():
        add_flash_message(request, "CPF já cadastrado no seu hotel", "danger")
        return RedirectResponse(url="/dashboard_guests/new", status_code=status.HTTP_303_SEE_OTHER)
    
    new_guest = Guest(
        name=name,
        cpf=cpf,
        email=email,
        phone_number=phone_number,
        hotel_id=hotel_id
    )

    db.add(new_guest)
    db.commit()
    db.refresh(new_guest)
    add_flash_message(request, "Hóspede cadastrado com sucesso, continue com a reserva", "success")
    return RedirectResponse(
        url=f"/dashboard_reservations/new?guest_id={new_guest.id}",
        status_code=303,
    )
