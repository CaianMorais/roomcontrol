# import de libs built-in
from typing import Optional

# import de libs third-party
from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

# import do current-app
from app.core.config import get_db
from app.core.security import generate_csrf_token, validate_csrf_token
from app.helpers.guest_access.access import find_guest, find_reservation, find_services
from app.helpers.guest_access.request_service import create_request_service
from app.models.guest import Guest
from app.models.reservations import Reservations
from app.models.services import Services
from app.utils.flash import add_flash_message, render

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(prefix="/guests", tags=["guests"])
api_router = APIRouter(prefix="/api", tags=["api_guests"])

@router.get('', response_class=HTMLResponse, include_in_schema=False)
def guest(
    request: Request,
):
    request.session.pop('guest_cpf', None)
    request.session.pop('reservation_id', None)
    
    csrf_token = generate_csrf_token(request)
    request.session['csrf_token'] = csrf_token
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
    token: str = Form(...),
    cpf: str = Form(...),
    res: str = Form(...),
    db: Session = Depends(get_db)
):
    if not token or token != request.session.get('csrf_token') or not validate_csrf_token(request, token):
        add_flash_message(request, 'Houve um problema ao processar sua sessão. Tente novamente.', 'danger')
        return RedirectResponse(request.url_for('guest'), status_code=303)
    
    guest = find_guest(request, db, cpf)
    if not guest:
        add_flash_message(request, 'Hóspede não encontrado.', 'danger')
        return RedirectResponse(request.url_for('guest'), status_code=303)
    
    reservation = find_reservation(request, db, res, guest)
    if not reservation:
        add_flash_message(request, 'Reserva não encontrada.', 'danger')
        return RedirectResponse(request.url_for('guest'), status_code=303)
    
    request.session["guest_cpf"] = guest.cpf
    request.session["reservation_id"] = reservation.Reservations.id

    return RedirectResponse(
        request.url_for('guest_panel'), status_code=303)

@router.get('/guest_panel', response_class=HTMLResponse, include_in_schema=False)
def guest_panel(
    request: Request,
    db: Session = Depends(get_db)
):
    reservation_id = request.session.get("reservation_id")
    if not reservation_id:
        add_flash_message(request, 'Reserva não encontrada na sessão. Por favor, faça login novamente.', 'danger')
        return RedirectResponse(request.url_for('guest'), status_code=303)
    
    guest_cpf = request.session.get("guest_cpf")
    if not guest_cpf:
        add_flash_message(request, 'Hóspede não encontrado na sessão. Por favor, faça login novamente.', 'danger')
        return RedirectResponse(request.url_for('guest'), status_code=303)
    
    guest = find_guest(request, db, guest_cpf)
    reservation = find_reservation(request, db, reservation_id, guest)
    services = find_services(db, reservation)

    return render(
        templates,
        request,
        'guests_access/reservation.html',
        {
            'guest': guest,
            'reserva': reservation,
            'services': services
        }
    )

@router.post('/request', include_in_schema=False)
def request_service(
    request: Request,
    service_description: str = Form(...),
    db: Session = Depends(get_db)
):
    reservation_id = request.session.get("reservation_id")
    if not reservation_id:
        add_flash_message(request, 'Reserva não encontrada na sessão. Por favor, faça login novamente.', 'danger')
        return RedirectResponse(request.url_for('guest'), status_code=303)
    
    new_request = create_request_service(request, db, reservation_id, service_description)

    if new_request:
        return JSONResponse({
            "ok": True,
            "message": "Solicitação de serviço recebida com sucesso.",
            "service_description": service_description
        })
    else:
        return JSONResponse({
            "ok": False,
            "message": "Algo deu errado com sua solicitação",
            "service_description": service_description
        })

@router.get('/load_request/{request_id}', include_in_schema=False)
def load_service_request(
    request: Request,
    request_id: int,
    db: Session = Depends(get_db)
):
    service_request = db.query(Services).filter(Services.id == request_id).first()
    if not service_request:
        return JSONResponse({
            "ok": False,
            "message": "Solicitação de serviço não encontrada."
        })
    
    return JSONResponse({
        "ok": True,
        "service_request": {
            "id": service_request.id,
            "request": service_request.request,
        }
    })