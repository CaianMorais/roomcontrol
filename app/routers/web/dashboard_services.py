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
from app.services.services_request_service import ServicesRequestService
from app.schemas.services import ServicesOut
from app.schemas.table_services import TableServicesOut
from app.utils.flash import add_flash_message, render
from app.utils.session_guard import require_session


router = APIRouter(
    prefix='/dashboard_services',
    tags=['services'],
    dependencies=[Depends(require_session)]
)

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

templates = Jinja2Templates(directory='app/templates')

###################### API START ######################
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
    query = (
        db.query(Services)
        .options(
            joinedload(Services.reservation).joinedload(Reservations.guest),
            joinedload(Services.reservation).joinedload(Reservations.room).joinedload(Rooms.hotel)
        )
    )

    if not access["is_global"]:
        query = query.join(Rooms, Services.room_id == Rooms.id).join(
            Hotel, Rooms.hotel_id == Hotel.id
        ).filter(Hotel.id == access["hotel_id"])
    else:
        if hotel_id:
            query = query.join(Rooms, Services.room_id == Rooms.id).join(
                Hotel, Rooms.hotel_id == Hotel.id
            ).filter(Hotel.id == hotel_id)
        if hotel_name:
            query = query.join(Rooms, Services.room_id == Rooms.id).join(
                Hotel, Rooms.hotel_id == Hotel.id
            ).filter(Hotel.name.ilike(f'%{hotel_name}%'))

    if reservation_id:
        query = query.filter(Services.reservation_id == reservation_id)
    if guest_cpf:
        query = query.join(Guest, Services.guest_id == Guest.id).filter(Guest.cpf == guest_cpf)
    if guest_name:
        query = query.join(Guest, Services.guest_id == Guest.id).filter(Guest.name.ilike(f'%{guest_name}%'))
    if room_number:
        query = query.join(Rooms, Services.room_id == Rooms.id).filter(Rooms.room_number == room_number)
    if status:
        query = query.filter(Services.status.ilike(f'%{status}%'))

    requests = query.all()

    if not requests:
        raise HTTPException(status_code=404, detail="Nenhum pedido encontrado")
    
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

###################### API END ######################

@router.get('', response_class=HTMLResponse, include_in_schema=False)
def services_requests(
    request: Request,
):
    # essa rota somente renderiza o template
    # o carregamento dos dados é feito via JS chamando a endpoint interna

    return render(
        templates,
        request,
        "dashboard/services/services.html"
    )

@router.get('/pedido/{request_id}', response_class=HTMLResponse, include_in_schema=False)
def view_request(
    request: Request,
    request_id: int,
    db: Session = Depends(get_db)
):
    service_request, error = ServicesRequestService.get_request(db, request.session.get('hotel_id'), request_id)
    if error:
        add_flash_message(request, error, "warning")
        return RedirectResponse(request.url_for('services_requests'), status_code=303)
    
    # seta o id do serviço na sessão para fazer update sem precisar passar o id pelo template
    request.session['service_id'] = service_request.Services.id

    return render(
        templates,
        request,
        "dashboard/services/view_request.html",
        {
            "service": service_request,
        }
    )
    
@router.post('/update_status', include_in_schema=False)
def update_service_status(
    request: Request,
    payload: dict = Body(...),
    db: Session = Depends(get_db)
):
    # resgata o novo status do body que JS envia
    new_status = payload.get("status")
    # resgata o id do pedido
    service_id = request.session.get('service_id')
    # chama a função de update passando o request, db, novo status e o id do peddio
    response = ServicesRequestService.update_request_status(request, db, new_status, service_id)

    if response["ok"]:
        AuditService.register(db, request.session.get("hotel_id"), 'update', 'service', service_id, request.session.get("collaborator_id"))
    
    return JSONResponse(
        {
            "ok": response["ok"],
            "message": response["message"],
            "new_status": response["new_status"]
        },
        status_code=200 if response["ok"] else 400
    )
    


    
