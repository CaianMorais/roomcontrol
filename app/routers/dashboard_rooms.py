# import de libs built-in
from decimal import Decimal
from typing import List, Optional

# import de libs third-party
from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload

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
    has_filter = False

    # valida o hotel
    if not hotel_id:
        add_flash_message(request, "Hotel não reconhecido", "warning")
        return RedirectResponse(url="/dashboard_rooms", status_code=303)

    # inicia a query
    query = db.query(Rooms).filter_by(hotel_id=hotel_id).filter(Rooms.is_deleted == False)

    ROOM_TYPE_MAP = tipos_map()
    ORDER_MAP = coluna_map()

    # MARCA AS FLAGS COM TRUE OU FALSE QUE FORAM MARCADAS NO FILTRO
    selected_type_flags = {
        "solteiro": solteiro,
        "duplo": duplo,
        "casal": casal,
        "triplo": triplo,
        "triplo_com_casal": triplo_com_casal,
        "personalizado": personalizado,
    }

    # ITERA SOBRE AS FLAGS PARA ADICIONAR RESGATAR O 
    # VALOR DOS SELECIONADOS (TRUE) NA LISTA TOOM_TYPE_MAP
    room_types = [t for flag, on in selected_type_flags.items() if on for t in ROOM_TYPE_MAP[flag]]
    if room_types:
        # SE TIVER ITENS NA LISTA, FAZ A CONSULTA
        query = query.filter(Rooms.type.in_(room_types))

    # MARCA AS FLAGS QUE FORAM MARCADAS NO FILTRO
    status_flags = {
        "available": available,
        "occupied": occupied,
        "maintenance": maintenance,
    }

    #ITERA SOBRE AS FLAGS PARA FAZER A LISTA DE STATUS SELECIONADOS NO FILTRO
    statuses = [name for name, on in status_flags.items() if on]
    if statuses:
        query = query.filter(Rooms.status.in_(statuses))

    # ORDENAÇÃO DOS QUARTOS, PRIORIZANDO OS ATIVOS ACIMA
    order_cols = [Rooms.is_active.desc()]

    # PEGA O CRITERIO DE ORDENAÇÃO NO FILTRO E BUSCA ELE NO MAPPING
    col = ORDER_MAP.get(criteria or "")
    if col is not None:
        # SE HOVER CRITERIO DE ORDENAÇÃO, PEGA A ORDENAÇÃO
        if order == "decres":
            order_cols.append(col.desc())
        else:
            # SENAO O PADRAO É ASC
            order_cols.append(col.asc())
    else:
        # SE NAO HOUVER CRITERIO DE ORDENAÇÃO
        # O PADRÃO SERÁ PELO NUMERO DO QUARTO CRESCENTE
        order_cols.append(Rooms.room_number.asc())

    query = query.order_by(*order_cols)

    rooms = query.all()

    # SE TIVER ALGUM FILTRO ATIVO, MUDA A VARIAVEL PRA SABER
    # SE HÁ QUARTOS NA VARIAVEL DA CONSULTA OU NÃO
    has_filter = bool(
        room_types or statuses or (criteria in ORDER_MAP)
    )
    if has_filter:
        if rooms:
            add_flash_message(request, f"Filtro aplicado: {len(rooms)} quartos encontrados.", "info")
        else:
            add_flash_message(request, "Nenhum quarto encontrado com esses filtros.", "warning")

    return render(
        templates,
        request,
        "dashboard/rooms/rooms.html",
        {
            "rooms": rooms,
            "has_filter": has_filter
        }
    )

@router.get("/new", response_class=HTMLResponse, include_in_schema=False)
def new_room(request: Request):
    csrf_token = generate_csrf_token(request)
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
    if not validate_csrf_token(request, csrf_token):
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
    room_capacities = room_capacities_map()
    
    if room_type in room_capacities:
        # pega as capacidades do quarto no map
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
    new_room = room_creator(request, hotel_id, room_number, room_type, capacity_adults, capacity_children,capacity_total, price, db)
    register_audit(db, hotel_id, 'create', 'room', new_room.id, request.session.get("collaborator_id"))
    return RedirectResponse(url="/dashboard_rooms", status_code=303)

@router.get("/edit/{room_id}", response_class=HTMLResponse, include_in_schema=False)
def edit_room(
    room_id: int,
    request: Request,
    db: Session = Depends(get_db),
    next: Optional[str] = Query(None),
):
    room = db.query(Rooms) \
        .filter_by(id=room_id, hotel_id=request.session.get("hotel_id")) \
        .filter(Rooms.is_deleted == False) \
        .first()

    if room.status == 'occupied':
        add_flash_message(request, "Apenas visualização, não é possível alterar quartos ocupados.", 'secondary')
    if room.hotel_id != request.session.get("hotel_id"):
        add_flash_message(request, "Quarto não encontrado.", "warning")
        return RedirectResponse(url="/dashboard_rooms", status_code=303)
    if not room:
        add_flash_message(request, "Quarto não encontrado.", "warning")
        return RedirectResponse(url="/dashboard_rooms", status_code=303)
    
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
        return RedirectResponse(url="/auth", status_code=303)

    # captura o hotel
    hotel_id = request.session.get("hotel_id")

    # valida o hotel
    if not hotel_id:
        add_flash_message(request, "Hotel não reconhecido", "warning")
        return RedirectResponse(url="/dashboard_rooms", status_code=303)

    # verifica se o quarto existe
    room = db.query(Rooms) \
        .filter_by(id=room_id, hotel_id=hotel_id) \
        .filter(Rooms.is_deleted == False) \
        .first()
    
    if not room:
        add_flash_message(request, "Quarto não encontrado.", "warning")
        return RedirectResponse(url="/dashboard_rooms", status_code=303)
    
    # verifica a disponibilidade do quarto
    if room.status == 'occupied':
        add_flash_message(request, "O quarto não pode ser modificado enquanto ele estiver ocupado", 'warning')
        return RedirectResponse(url="/dashboard_rooms", status_code=303)
    
    # se está ativo e o formulário traz mudança nesse parametro
    if room.is_active == True and room.is_active != is_active:
        # consulta se há alguma reserva ativa para esse quarto
        reservation = db.query(Reservations) \
        .filter_by(room_id=room.id) \
        .all()
        for res in reservation:
            if res.status in ['booked', 'checked_in']:
                add_flash_message(request, "O quarto não pode ser desativado pois possui reservas ativas.", 'warning')
                return RedirectResponse(url="/dashboard_rooms", status_code=303)
    
    # define a capacidade com base no tipo do quarto (pra não depender dos dados do form)
    room_capacities = room_capacities_map()
    
    if room_type in room_capacities:
        # pega as capacidades do quarto no map
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
    room = room_editor(request, room, room_number, room_type, capacity_adults, capacity_children, capacity_total, price, is_active, comments, db)
    register_audit(db, hotel_id, 'update', 'room', room.id, request.session.get("collaborator_id"))
    if next:
        return RedirectResponse(url=next, status_code=303)
    return RedirectResponse(url="/dashboard_rooms", status_code=303)

@router.get("/delete/{room_id}", include_in_schema=False)
def delete_room(room_id: int, request: Request, db: Session = Depends(get_db
)):
    room = db.query(Rooms) \
        .filter_by(id=room_id, hotel_id=request.session.get("hotel_id")) \
        .filter(Rooms.is_deleted == False) \
        .first()

    if not room:
        add_flash_message(request, "Quarto não encontrado.", "warning")
        return RedirectResponse(url="/dashboard_rooms", status_code=303)
    if room.hotel_id != request.session.get("hotel_id"):
        add_flash_message(request, "Quarto não encontrado.", "warning")
        return RedirectResponse(url="/dashboard_rooms", status_code=303)
    if room.status == 'occupied':
        add_flash_message(request, "O quarto não pode ser modificado enquanto ele estiver ocupado", 'warning')
        return RedirectResponse(url="/dashboard_rooms", status_code=303)
    
    room.is_deleted = True
    db.commit()
    register_audit(db, room.hotel_id, 'delete', 'room', room.id, request.session.get("collaborator_id"))
    add_flash_message(request, f"Quarto {room.room_number} excluído com sucesso.", "success")
    return RedirectResponse(url="/dashboard_rooms", status_code=303)