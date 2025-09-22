from decimal import Decimal
from app.core.config import SessionLocal
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Form, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from passlib.hash import bcrypt

from app.utils.flash import add_flash_message, render
from app.utils.session_guard import require_session
from app.schemas.rooms import RoomOut, RoomCreate, RoomsBase
from app.models.rooms import Rooms

router = APIRouter(
    prefix="/dashboard_rooms",
    tags=["rooms"],
    dependencies=[Depends(require_session)]
)

api_router = APIRouter(prefix="/api", tags=["api_rooms"])
templates = Jinja2Templates(directory="app/templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@api_router.get("/get_rooms", response_model=List[RoomOut])
def get_rooms(
    hotel_id: Optional[str] = Query(None, description="Filtrar pelo ID do hotel"),
    db: Session = Depends(get_db)
):
    query = db.query(Rooms)

    if hotel_id:
        query = query.filter(Rooms.hotel_id == hotel_id)

    rooms = query.all()

    if not rooms:
        raise HTTPException(status_code=404, detail="Nenhum quarto encontrado")
    
    return rooms

@router.get("", response_class=HTMLResponse, include_in_schema=False)
def rooms(request: Request, db: Session = Depends(get_db)):
    query = db.query(Rooms).filter_by(hotel_id=request.session.get("hotel_id")).all()
    return render(templates, request, "dashboard/rooms/rooms.html", {"rooms": query})

@router.get("/new", response_class=HTMLResponse, include_in_schema=False)
def new_room(request: Request):
    return render(templates, request, "dashboard/rooms/new_room.html")

@router.post("/new", response_class=HTMLResponse, include_in_schema=False)
def create_room(
    request: Request,
    room_number: str = Form(...),
    room_type: str = Form(...),
    capacity_adults: int = Form(0),
    capacity_children: int = Form(0),
    capacity_total: int= Form(0),
    price: float = Form(0.0),
    db: Session = Depends(get_db)
):
    hotel_id = request.session.get("hotel_id")

    if not hotel_id:
        add_flash_message(request, "Hotel não reconhecido", "warning")
        return RedirectResponse(url="/dashboard_rooms", status_code=303)

    existing_room = db.query(Rooms).filter_by(hotel_id=hotel_id, room_number=room_number).first()
    if existing_room:
        add_flash_message(request, f"Um quarto com o número {room_number} já existe.", "warning")
        return RedirectResponse(url="/dashboard_rooms", status_code=303)

    if room_type == "1":
        capacity_adults = 1
        capacity_children = 0
    elif room_type == "2":
        capacity_adults = 2
        capacity_children = 0
    elif room_type == "'3'":
        capacity_adults = 2
        capacity_children = 0
    elif room_type == "4":
        capacity_adults = 3
        capacity_children = 0
    elif room_type == "5":
        capacity_adults = 4
        capacity_children = 0
    elif room_type == "6":
        capacity_adults = 2
        capacity_children = 2
    elif room_type == "Personalizado":
        if capacity_adults is None or capacity_children is None:
            add_flash_message(request, "É necessário preencher a capacidade de adultos e crianças.", "warning")
            return RedirectResponse(url="/dashboard_rooms", status_code=303)
    else:
        add_flash_message(request, "Tipo de quarto é inválido.", "warning")
        return RedirectResponse(url="/dashboard_rooms", status_code=303)
    
    capacity_total = capacity_adults + capacity_children

    price = Decimal(price)
    
    new_room = Rooms(
        hotel_id=hotel_id,
        room_number=room_number,
        type=room_type,
        capacity_adults=capacity_adults,
        capacity_children=capacity_children,
        capacity_total=capacity_total,
        price=price,
        status='available',
        is_active=True
    )

    db.add(new_room)
    db.commit()
    db.refresh(new_room)
    add_flash_message(request, f"Quarto {room_number} criado com sucesso.", "success")
    return render(
        templates,
        request,
        "dashboard/rooms/new_room.html"
    )