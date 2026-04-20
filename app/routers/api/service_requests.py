# import de libs built-in
from typing import List, Literal, Optional

# import de libs third-party
from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload

# import do current-app
from app.core.config import get_db
from app.core.dependencies import get_api_access
from app.models.guest import Guest
from app.models.hotel import Hotel
from app.models.reservations import Reservations
from app.models.rooms import Rooms
from app.models.services import Services
from app.services.audit_service import AuditService
from app.services.services_request_service import ApiServicesRequestService
from app.schemas.services import ServicesOut
from app.schemas.table_services import TableServicesOut
from app.utils.flash import add_flash_message, render
from app.utils.session_guard import require_session

# configuração dos routers
api_router = APIRouter(
    prefix='/api',
    tags=['services'],
    dependencies=[Depends(get_api_access)]
)
internal_api_router = APIRouter(
    prefix='/internal_api',
    tags=['services'],
    dependencies=[Depends(require_session)]
)


@api_router.get('/services_requests', response_model=List[ServicesOut], summary="Filtrar pedidos de serviços")
def get_services_requests(
    access: dict = Depends(get_api_access),
    reservation_id: Optional[int] = Query(None, description="Filtrar pelo número da reserva"),
    guest_cpf: Optional[int] = Query(None, description="Filtrar pelo CPF do hóspede"),
    guest_name: Optional[str] = Query(None, description="Filtrar pelo nome do hóspede"),
    room_number: Optional[str] = Query(None, description="Filtrar pelo número do quarto"),
    status: Optional[Literal['pending', 'in_progress', 'completed']] = Query(None, description="Filtrar pelo status do pedido"),
    hotel_id: Optional[int] = Query(None, description="Filtrar pelo ID do hotel (FUNCIONAL SOMENTE PARA CHAVE GLOBAL)"),
    hotel_name: Optional[str] = Query(None, description="Filtrar pelo nome do hotel (FUNCIONAL SOMENTE PARA CHAVE GLOBAL)"),
    db: Session = Depends(get_db)
):      
    if not access["is_global"]:
        query = ApiServicesRequestService.get_requests(db, access["hotel_id"])
    else:
        query = ApiServicesRequestService.get_requests(db, None)
        if hotel_id or hotel_name:
            query = ApiServicesRequestService.filter_requests(query, hotel_id, hotel_name)

    if reservation_id or guest_cpf or guest_name or room_number or status:
        query = ApiServicesRequestService.filter_requests(
            query,
            reservation_id=reservation_id,
            guest_cpf=guest_cpf,
            guest_name=guest_name,
            room_number=room_number,
            status=status
        )

    requests = query.all()

    if not requests:
        requests=[]
    
    return requests

@internal_api_router.get('/table_services_requests', response_model=List[TableServicesOut], include_in_schema=False)
def get_table_services_requests(
    request: Request,
    db: Session = Depends(get_db)
):
    hotel_id = request.session.get("hotel_id")

    if not hotel_id:
        raise HTTPException(status_code=400, detail="Hotel não reconhecido")

    query = (
        db.query(Services)
        .options(
            joinedload(Services.reservation).joinedload(Reservations.guest),
            joinedload(Services.reservation).joinedload(Reservations.room).joinedload(Rooms.hotel)
        )
        .join(Rooms, Services.room_id == Rooms.id)
        .join(Hotel, Rooms.hotel_id == Hotel.id)
        .filter(Hotel.id == hotel_id)
    )

    requests = query.all()

    if not requests:
        return []
    
    return requests

