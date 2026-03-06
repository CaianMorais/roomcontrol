# import de libs built-in
from decimal import Decimal
from typing import List, Optional

# import de libs third-party
from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import paginate as sa_paginate

# import do current-app
from app.core.config import get_db
from app.core.dependencies import get_api_access
from app.core.security import generate_csrf_token, validate_csrf_token
from app.helpers.register_audit import register_audit
from app.helpers.rooms.object_mapper import coluna_map, room_capacities_map, tipos_map
from app.helpers.rooms.room_creator import room_creator
from app.helpers.rooms.room_editor import room_editor
from app.models.hotel import Hotel
from app.models.reservations import Reservations
from app.models.rooms import Rooms
from app.schemas.rooms import RoomOut
from app.utils.flash import add_flash_message, render
from app.utils.session_guard import require_session

from app.services.room_service import RoomsService

router = APIRouter(
    prefix="/dashboard_rooms",
    tags=["rooms"],
    dependencies=[Depends(require_session)]
)

api_router = APIRouter(
    prefix="/api",
    tags=["rooms"],
    dependencies=[Depends(get_api_access)]
)

internal_api_router = APIRouter(
    prefix="/internal_api",
    tags=["rooms"],
    dependencies=[Depends(require_session)]
)

templates = Jinja2Templates(directory="app/templates")

@api_router.get("/rooms", response_model=List[RoomOut], summary="Filtrar quartos")
def get_rooms(
    access: dict = Depends(get_api_access),
    hotel_name: Optional[str] = Query(None, description="Filtrar pelo nome do hotel (FUNCIONAL SOMENTE PARA CHAVE GLOBAL)"),
    hotel_id: Optional[int] = Query(None, description="Filtrar pelo ID do hotel (FUNCIONAL SOMENTE PARA CHAVE GLOBAL)"),
    db: Session = Depends(get_db)
):
    query = db.query(Rooms).options(joinedload(Rooms.hotel))

    if not access["is_global"]:
        query = query.filter(Rooms.hotel_id == access["hotel_id"])

    if access["is_global"]:
        if hotel_name:
            query = query.filter(Hotel.name.ilike(f"%{hotel_name}%"))
        if hotel_id:
            query = query.filter(Hotel.id == hotel_id)

    rooms = query.all()

    if not rooms:
        raise HTTPException(status_code=404, detail="Nenhum quarto encontrado")
    
    return rooms

@internal_api_router.get("/rooms", include_in_schema=False)
def get_rooms_for_reservations_filter(
    request: Request,
    db: Session = Depends(get_db)
):
    hotel_id = request.session.get("hotel_id")
    if not hotel_id:
        raise HTTPException(status_code=400, detail="Hotel não reconhecido")
    
    rooms = db.query(Rooms) \
        .options(joinedload(Rooms.hotel)) \
        .filter(Rooms.is_deleted == False) \
        .filter(Rooms.hotel_id == hotel_id) \
        .all()

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
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
):
    # captura o hotel
    hotel_id = request.session.get("hotel_id")
    has_filter = False

    # valida o hotel
    if not hotel_id:
        add_flash_message(request, "Hotel não reconhecido", "warning")
        return RedirectResponse(url="/dashboard_rooms", status_code=303)

    # usa a service para fazer a query
    query = RoomsService.list_rooms(db, hotel_id)

    if criteria or order or solteiro or duplo or casal or triplo or triplo_com_casal or personalizado or available or occupied or maintenance:
        query, has_filter = RoomsService.filter_rooms(query, solteiro, duplo, casal, triplo, triplo_com_casal, personalizado, available, occupied, maintenance, criteria, order)

    # paginação
    params = Params(page=page, size=per_page)
    page_obj = sa_paginate(db, query, params)

    return render(
        templates,
        request,
        "dashboard/rooms/rooms.html",
        {
            "rooms": page_obj.items,
            "pager": {
                "page": page_obj.page,
                "pages": page_obj.pages,
                "per_page": page_obj.size,
                "total": page_obj.total,
            },
            "has_filter": has_filter,
            "criteria": criteria,
            "order": order,
            "solteiro": solteiro,
            "duplo": duplo,
            "casal": casal,
            "triplo": triplo,
            "triplo_com_casal": triplo_com_casal,
            "personalizado": personalizado,
            "available": available,
            "occupied": occupied,
            "maintenance": maintenance
        }
    )

@router.get("/new", response_class=HTMLResponse, include_in_schema=False)
def new_room(request: Request):
    csrf_token = generate_csrf_token(request)
    return render(
        templates,
        request,
        "dashboard/rooms/new_room.html",
        {
            "csrf_token": csrf_token
        }
    )

@router.post("/new", response_class=HTMLResponse, include_in_schema=False)
def create_room(
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
    if not validate_csrf_token(request, csrf_token):
        add_flash_message(request, "Token de segurança invéliado, operação finalizada.", "danger")
        return RedirectResponse(url=request.url_for("new_room"), status_code=303)
    
    # captura o hotel
    hotel_id = request.session.get("hotel_id")

    # valida o hotel
    if not hotel_id:
        add_flash_message(request, "Hotel não reconhecido", "warning")
        return RedirectResponse(url=request.url_for("rooms"), status_code=303)

    # Service que cria o quarto, já com as validações necessárias
    room, error = RoomsService.create_room(db, hotel_id, room_number, room_type, capacity_adults, capacity_children, capacity_total, price, is_active, comments)

    if error:
        add_flash_message(request, error, "danger")
        return RedirectResponse(url=request.url_for("new_room"), status_code=303)
    
    # registra log
    register_audit(db, hotel_id, 'create', 'room', room.id, request.session.get("collaborator_id"))
    add_flash_message(request, f"Quarto {room.room_number} criado com sucesso.", "success")

    return RedirectResponse(
        url=request.url_for("rooms"),
        status_code=303
    )

@router.get("/edit/{room_id}", response_class=HTMLResponse, include_in_schema=False)
def edit_room(
    room_id: int,
    request: Request,
    db: Session = Depends(get_db),
    next: Optional[str] = Query(None),
):
    # captura e valida o hotel
    hotel_id = request.session.get("hotel_id")
    if not hotel_id:
        add_flash_message(request, "Hotel não reconhecido", "warning")
        return RedirectResponse(url=request.url_for("rooms"), status_code=303)
    
    # localiza o quarto
    room, error = RoomsService.get_room(db, room_id, hotel_id)

    if error:
        add_flash_message(request, error, "warning")
        return RedirectResponse(url=request.url_for("rooms"), status_code=303)
    
    # gera o token
    csrf_token = generate_csrf_token(request)

    return render(
        templates, 
        request, 
        "dashboard/rooms/edit_room.html", 
        {
            "room": room, 
            "csrf_token": csrf_token,
            "next": next
        }
    )

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
    next: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    # valida o CSRF token
    if not validate_csrf_token(request, csrf_token):
        add_flash_message(request, "Token de segurança invéliado, operação finalizada.", "danger")
        return RedirectResponse(url=request.url_for("rooms"), status_code=303)

    # captura e valida o hotel
    hotel_id = request.session.get("hotel_id")
    if not hotel_id:
        add_flash_message(request, "Hotel não reconhecido", "warning")
        return RedirectResponse(url=request.url_for("rooms"), status_code=303)

    # verifica se o quarto existe
    room, error = RoomsService.get_room(db, room_id, hotel_id)
    if error:
        add_flash_message(request, error, "warning")
        return RedirectResponse(url=request.url_for("rooms"), status_code=303)
    
    # se o quarto existe, tenta atualizar usando a service
    room, error = RoomsService.update_room(db, room, room_number, room_type, capacity_adults, capacity_children, capacity_total, price, is_active, comments)
    if error:
        add_flash_message(request, error, "warning")
        return RedirectResponse(url=request.url_for("rooms"), status_code=303)

    register_audit(db, hotel_id, 'update', 'room', room.id, request.session.get("collaborator_id"))
    add_flash_message(request, f"Quarto {room.room_number} atualizado com sucesso.", "success")

    if next:
        return RedirectResponse(url=next, status_code=303)
    return RedirectResponse(url="/dashboard_rooms", status_code=303)

@router.get("/delete/{room_id}", include_in_schema=False)
def delete_room(room_id: int, request: Request, db: Session = Depends(get_db
)):
    # captura e valida o hotel
    hotel_id = request.session.get("hotel_id")
    if not hotel_id:
        add_flash_message(request, "Hotel não reconhecido", "warning")
        return RedirectResponse(url=request.url_for("rooms"), status_code=303)
    
    # instancia o quarto e valida se existe
    room, error = RoomsService.get_room(db, room_id, hotel_id)

    if error:
        add_flash_message(request, error, "warning")
        return RedirectResponse(url=request.url_for("rooms"), status_code=303)
    
    # usa a service para deletar e valida se é possivel
    deleted_room, error = RoomsService.delete_room(db, room)
    if error and not deleted_room:
        add_flash_message(request, error, "warning")
        return RedirectResponse(url=request.url_for("rooms"), status_code=303)

    # registra log
    register_audit(db, room.hotel_id, 'delete', 'room', room.id, request.session.get("collaborator_id"))
    add_flash_message(request, f"Quarto {room.room_number} excluído com sucesso.", "success")

    return RedirectResponse(url="/dashboard_rooms", status_code=303)