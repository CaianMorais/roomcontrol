# import de libs third-party
from fastapi import APIRouter, Body, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

# import do current-app
from app.core.config import get_db
from app.services.audit_service import AuditService
from app.services.services_request_service import ServicesRequestService
from app.utils.flash import add_flash_message, render
from app.utils.session_guard import require_session

# configuração do router e templates
router = APIRouter(
    prefix='/dashboard_services',
    tags=['services'],
    dependencies=[Depends(require_session)]
)
templates = Jinja2Templates(directory='app/templates')


@router.get('', response_class=HTMLResponse, include_in_schema=False)
def services_requests(
    request: Request,
):
    # essa rota somente renderiza o template
    # o carregamento dos dados é feito via JS chamando a endpoint interna
    # endpoint interno: /routers/api/service_requests.py: @internal_api_router

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
    


    
