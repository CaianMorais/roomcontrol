# import de libs third-party
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

# import do current-app
from app.core.config import get_db
from app.core.security import generate_csrf_token, validate_csrf_token
from app.services.guest_access_service import GuestAccessService
from app.utils.flash import add_flash_message, render

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(prefix="/guests", tags=["guests"])
api_router = APIRouter(prefix="/api", tags=["api_guests"])


@router.get('', response_class=HTMLResponse, include_in_schema=False)
def guest(request: Request):
    request.session.pop('guest_cpf', None)
    request.session.pop('reservation_id', None)

    csrf_token = generate_csrf_token(request)
    return render(
        templates,
        request,
        'auth/guest_access.html',
        {'csrf_token': csrf_token}
    )


@router.post('/access', response_class=HTMLResponse, include_in_schema=False)
def guest_access(
    request: Request,
    token: str = Form(...),
    cpf: str = Form(...),
    res: str = Form(...),
    db: Session = Depends(get_db)
):
    if not validate_csrf_token(request, token):
        add_flash_message(request, 'Houve um problema ao processar sua sessão. Tente novamente.', 'danger')
        return RedirectResponse(request.url_for('guest'), status_code=303)

    guest, error = GuestAccessService.get_guest_by_cpf(db, cpf)
    if error:
        add_flash_message(request, error, 'danger')
        return RedirectResponse(request.url_for('guest'), status_code=303)

    reservation, error = GuestAccessService.get_active_reservation(db, int(res), guest.id)
    if error:
        add_flash_message(request, error, 'danger')
        return RedirectResponse(request.url_for('guest'), status_code=303)

    request.session['guest_cpf'] = guest.cpf
    request.session['reservation_id'] = reservation.Reservations.id

    return RedirectResponse(request.url_for('guest_panel'), status_code=303)


@router.get('/guest_panel', response_class=HTMLResponse, include_in_schema=False)
def guest_panel(
    request: Request,
    db: Session = Depends(get_db)
):
    reservation_id = request.session.get('reservation_id')
    guest_cpf = request.session.get('guest_cpf')

    if not reservation_id or not guest_cpf:
        add_flash_message(request, 'Sessão expirada. Por favor, faça login novamente.', 'danger')
        return RedirectResponse(request.url_for('guest'), status_code=303)

    guest, error = GuestAccessService.get_guest_by_cpf(db, guest_cpf)
    if error:
        add_flash_message(request, error, 'danger')
        return RedirectResponse(request.url_for('guest'), status_code=303)

    reservation, error = GuestAccessService.get_active_reservation(db, reservation_id, guest.id)
    if error:
        add_flash_message(request, error, 'danger')
        return RedirectResponse(request.url_for('guest'), status_code=303)

    services = GuestAccessService.get_services(db, reservation_id)

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
    reservation_id = request.session.get('reservation_id')
    if not reservation_id:
        add_flash_message(request, 'Sessão expirada. Por favor, faça login novamente.', 'danger')
        return RedirectResponse(request.url_for('guest'), status_code=303)

    service, error = GuestAccessService.create_service_request(db, reservation_id, service_description)

    if error:
        return JSONResponse(
            status_code=400,
            content={
                'ok': False,
                'message': error,
                'service_description': service_description
            }
        )

    return JSONResponse({
        'ok': True,
        'message': 'Solicitação de serviço recebida com sucesso.',
        'service_description': service_description
    })


@router.get('/load_request/{request_id}', include_in_schema=False)
def load_service_request(
    request: Request,
    request_id: int,
    db: Session = Depends(get_db)
):
    service, error = GuestAccessService.get_service_by_id(db, request_id)

    if error:
        return JSONResponse(
            status_code=404,
            content={'ok': False, 'message': error}
        )

    return JSONResponse({
        'ok': True,
        'service_request': {
            'id': service.id,
            'request': service.request,
        }
    })