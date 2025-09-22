from decimal import Decimal
from app.core.config import SessionLocal
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Form, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from passlib.hash import bcrypt

from app.core.security import generate_csrf_token, validate_csrf_token
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
def rooms(
    request: Request,
    criteria: Optional[str] = Query("", description="Critério de ordenação"),
    order: Optional[str] = Query("", description="Ordem de exibição"),
    solteiro: Optional[bool] = Query(False),
    duplo: Optional[bool] = Query(False),
    casal: Optional[bool] = Query(False),
    triplo: Optional[bool] = Query(False),
    triplo_com_casal: Optional[bool] = Query(False),
    personalizado: Optional[bool] = Query(False),
    available: Optional[bool] = Query(False),
    occupied: Optional[bool] = Query(False),
    maintenance: Optional[bool] = Query(False),
    db: Session = Depends(get_db)
):
    
    # captura o hotel
    hotel_id = request.session.get("hotel_id")

    # valida o hotel
    if not hotel_id:
        add_flash_message(request, "Hotel não reconhecido", "warning")
        return RedirectResponse(url="/dashboard_rooms", status_code=303)

    # inicia a query
    query = db.query(Rooms).filter_by(hotel_id=hotel_id)
    if not query.first():
        return render(
            templates,
            request,
            "dashboard/rooms/rooms.html",
            {
                "rooms": [],
                "has_filter": False
            }
        )

    # aplica os filtros
    room_types = []
    if solteiro:
        room_types.append("1")
    if duplo:
        room_types.append("2")
        room_types.append("3")
    if casal:
        room_types.append("4")
    if triplo:
        room_types.append("5")
        room_types.append("6")
        room_types.append("7")
    if triplo_com_casal:
        room_types.append("8")
    if personalizado:
        room_types.append("9")
    
    if room_types:
        query = query.filter(Rooms.type.in_(room_types))

    # filtra pela situação
    statuses = []
    if available:
        statuses.append("available")
    if occupied:
        statuses.append("occupied")
    if maintenance:
        statuses.append("maintenance")

    if statuses:
        query = query.filter(Rooms.status.in_(statuses))

    # aplica a ordenação
    if criteria == "room_number":
        if order == "cres":
            query = query.order_by(Rooms.room_number.asc())
        elif order == "decres":
            query = query.order_by(Rooms.room_number.desc())
    elif criteria == "capacity_total":
        if order == "cres":
            query = query.order_by(Rooms.capacity_total.asc())
        elif order == "decres":
            query = query.order_by(Rooms.capacity_total.desc())
    elif criteria == "capacity_adults":
        if order == "cres":
            query = query.order_by(Rooms.capacity_adults.asc())
        elif order == "decres":
            query = query.order_by(Rooms.capacity_adults.desc())
    elif criteria == "capacity_children":
        if order == "cres":
            query = query.order_by(Rooms.capacity_children.asc())
        elif order == "decres":
            query = query.order_by(Rooms.capacity_children.desc())
    elif criteria == "price":
        if order == "cres":
            query = query.order_by(Rooms.price.asc())
        elif order == "decres":
            query = query.order_by(Rooms.price.desc())

    # executa a query
    rooms = query.all()
    if not rooms:
        add_flash_message(request, "Nenhum quarto encontrado com esses filtros.", "warning")
        return RedirectResponse(url="/dashboard_rooms", status_code=303)
    if criteria or order or room_types or statuses:
        has_filter = True
        add_flash_message(request, f"Filtro aplicado: {len(rooms)} quartos encontrados.", "info")
    return render(
        templates,
        request,
        "dashboard/rooms/rooms.html",
        {
            "rooms": rooms,
            "has_filter": has_filter if (criteria or order or room_types or statuses) else False
        }
    )

@router.get("/new", response_class=HTMLResponse, include_in_schema=False)
def new_room(request: Request):
    csrf_token = generate_csrf_token()
    return render(templates, request, "dashboard/rooms/new_room.html", {"csrf_token": csrf_token})

@router.post("/new", response_class=HTMLResponse, include_in_schema=False)
def create_room(
    request: Request,
    room_number: str = Form(...),
    room_type: str = Form(...),
    capacity_adults: int = Form(0),
    capacity_children: int = Form(0),
    capacity_total: int= Form(0),
    price: float = Form(0.0),
    csrf_token: str = Form(...),
    db: Session = Depends(get_db)
):
    # valida o CSRF token
    if not validate_csrf_token(csrf_token):
        add_flash_message(request, "Token de segurança invéliado, operação finalizada.", "danger")
        return RedirectResponse(url="/auth", status_code=303)
    
    # captura o hotel
    hotel_id = request.session.get("hotel_id")

    # valida o hotel
    if not hotel_id:
        add_flash_message(request, "Hotel não reconhecido", "warning")
        return RedirectResponse(url="/dashboard_rooms", status_code=303)

    # verifica se já não existe um quarto com esse mesmo numero
    existing_room = db.query(Rooms).filter_by(hotel_id=hotel_id, room_number=room_number).first()
    if existing_room:
        add_flash_message(request, f"Um quarto com o número {room_number} já existe.", "warning")
        return RedirectResponse(url="/dashboard_rooms", status_code=303)

    # define a capacidade com base no tipo do quarto (pra não depender dos dados do form)
    room_capacities = {
    "1": [1, 0],
    "2": [1, 1],
    "3": [2, 0],
    "4": [2, 0],
    "5": [1, 2],
    "6": [2, 1],
    "7": [3, 0],
    "8": [2, 1],
}
    
    if room_type in room_capacities:
        capacity_adults, capacity_children = room_capacities[room_type]
    elif room_type == "9":
        # se o tipo for personalizado, depende dos dados do form
        if capacity_adults is None or capacity_children is None:
            add_flash_message(request, "É necessário preencher a capacidade de adultos e crianças.", "warning")
            return RedirectResponse(url="/dashboard_rooms", status_code=303)
    else:
        add_flash_message(request, "Tipo de quarto é inválido.", "warning")
        return RedirectResponse(url="/dashboard_rooms", status_code=303)
    
    # calcula a capacidade total após definir a capacidade
    capacity_total = capacity_adults + capacity_children

    # formata o preço pra decimal
    price = Decimal(price)
    
    # instancia o novo quarto
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

    # salva no banco
    db.add(new_room)
    db.commit()
    db.refresh(new_room)
    add_flash_message(request, f"Quarto {room_number} criado com sucesso. Clique <a href='/dashboard_rooms/edit/{new_room.id}'>aqui</a> para editá-lo.", "success")
    return RedirectResponse(url="/dashboard_rooms", status_code=303)

@router.get("/edit/{room_id}", response_class=HTMLResponse, include_in_schema=False)
def edit_room(room_id: int, request: Request, db: Session = Depends(get_db)):
    room = db.query(Rooms).filter_by(id=room_id, hotel_id=request.session.get("hotel_id")).first()
    if room.hotel_id != request.session.get("hotel_id"):
        add_flash_message(request, "Quarto não encontrado.", "warning")
        return RedirectResponse(url="/dashboard_rooms", status_code=303)
    if not room:
        add_flash_message(request, "Quarto não encontrado.", "warning")
        return RedirectResponse(url="/dashboard_rooms", status_code=303)
    csrf_token = generate_csrf_token()
    return render(templates, request, "dashboard/rooms/edit_room.html", {"room": room, "csrf_token": csrf_token})

@router.post("/edit/{room_id}", response_class=HTMLResponse, include_in_schema=False)
def update_room(
    room_id: int,
    request: Request,
    room_number: str = Form(...),
    room_type: str = Form(...),
    capacity_adults: int = Form(0),
    capacity_children: int = Form(0),
    capacity_total: int= Form(0),
    price: float = Form(0.0),
    is_active: Optional[bool] = Form(False),
    comments: Optional[str] = Form(""),
    csrf_token: str = Form(...),
    db: Session = Depends(get_db)
):
    # valida o CSRF token
    if not validate_csrf_token(csrf_token):
        add_flash_message(request, "Token de segurança invéliado, operação finalizada.", "danger")
        return RedirectResponse(url="/auth", status_code=303)

    # captura o hotel
    hotel_id = request.session.get("hotel_id")

    # valida o hotel
    if not hotel_id:
        add_flash_message(request, "Hotel não reconhecido", "warning")
        return RedirectResponse(url="/dashboard_rooms", status_code=303)

    # verifica se o quarto existe
    room = db.query(Rooms).filter_by(id=room_id, hotel_id=hotel_id).first()
    if not room:
        add_flash_message(request, "Quarto não encontrado.", "warning")
        return RedirectResponse(url="/dashboard_rooms", status_code=303)
    
    # define a capacidade com base no tipo do quarto (pra não depender dos dados do form)
    room_capacities = {
        "1": [1, 0],
        "2": [1, 1],
        "3": [2, 0],
        "4": [2, 0],
        "5": [1, 2],
        "6": [2, 1],
        "7": [3, 0],
        "8": [2, 1],
    }
    
    if room_type in room_capacities:
        capacity_adults, capacity_children = room_capacities[room_type]
    elif room_type == "9":
        # se o tipo for personalizado, depende dos dados do form
        if capacity_adults is None or capacity_children is None:
            add_flash_message(request, "É necessário preencher a capacidade de adultos e crianças.", "warning")
            return RedirectResponse(url="/dashboard_rooms", status_code=303)
    else:
        add_flash_message(request, "Tipo de quarto é inválido.", "warning")
        return RedirectResponse(url="/dashboard_rooms", status_code=303)
    
    # calcula a capacidade total após definir a capacidade
    capacity_total = capacity_adults + capacity_children
    
    # formata o preço pra decimal
    price = Decimal(price)

    # atualiza os dados do quarto
    room.room_number = room_number
    room.type = room_type
    room.capacity_adults = capacity_adults
    room.capacity_children = capacity_children
    room.capacity_total = capacity_total
    room.price = price
    room.is_active = is_active
    room.comments = comments

    db.commit()
    db.refresh(room)
    add_flash_message(request, f"Quarto {room.room_number} atualizado com sucesso.", "success")
    return RedirectResponse(url="/dashboard_rooms", status_code=303)

@router.get("/delete/{room_id}", include_in_schema=False)
def delete_room(room_id: int, request: Request, db: Session = Depends(get_db
)):
    room = db.query(Rooms).filter_by(id=room_id, hotel_id=request.session.get("hotel_id")).first()
    if not room:
        add_flash_message(request, "Quarto não encontrado.", "warning")
        return RedirectResponse(url="/dashboard_rooms", status_code=303)
    if room.hotel_id != request.session.get("hotel_id"):
        add_flash_message(request, "Quarto não encontrado.", "warning")
        return RedirectResponse(url="/dashboard_rooms", status_code=303)
    
    db.delete(room)
    db.commit()
    add_flash_message(request, f"Quarto {room.room_number} excluído com sucesso.", "success")
    return RedirectResponse(url="/dashboard_rooms", status_code=303)