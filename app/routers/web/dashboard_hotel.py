from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional

from app.core.config import get_db
from app.core.security import generate_csrf_token, validate_csrf_token
from app.repositories.auth_hotel_repository import HotelRepository
from app.services.auth_hotel_service import AuthHotelService
from app.utils.flash import add_flash_message, render
from app.utils.session_guard import require_session

router = APIRouter(
    prefix="/dashboard_hotel",
    tags=["hotel_profile"],
    dependencies=[Depends(require_session)]
)

templates = Jinja2Templates(directory="app/templates")

@router.get("/profile", response_class=HTMLResponse, include_in_schema=False)
def profile(request: Request, db: Session = Depends(get_db)):

    hotel_id = request.session.get("hotel_id")
    hotel = HotelRepository.find_by_id(db, hotel_id)
    
    if not request.session.get("collaborator_id"):
        csrf_token = generate_csrf_token(request)
    else:
        csrf_token = None
    
    return render(
        templates,
        request,
        "dashboard/hotel/hotel.html",
        {
            "hotel": hotel,
            "csrf_token": csrf_token
        }
    )

@router.post("/profile", include_in_schema=False)
async def update_hotel_profile(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    login: str = Form(...),
    phone_number: str = Form(...),
    zip_code: str = Form(...),
    address: str = Form(...),
    number: str = Form(...),
    city: str = Form(...),
    state: str = Form(...),
    password: Optional[str] = Form(None),
    confirm_password: Optional[str] = Form(None),
    csrf_token: str = Form(...),
    db: Session = Depends(get_db)
):
    if not validate_csrf_token(request, csrf_token):
        add_flash_message(request, "Token de segurança inválido.", "danger")
        return RedirectResponse(url=request.url_for("profile"), status_code=303)

    hotel_id = request.session.get("hotel_id")

    hotel, error = AuthHotelService.update_profile(
        db=db,
        hotel_id=hotel_id,
        name=name,
        email=email,
        login=login,
        phone_number=phone_number,
        zip_code=zip_code,
        address=address,
        number=number,
        city=city,
        state=state,
        password=password if password else None,
        confirm_password=confirm_password if confirm_password else None
    )

    if error:
        add_flash_message(request, error, "danger")
        return RedirectResponse(url=request.url_for("profile"), status_code=303)

    # atualiza o nome na sessão caso tenha mudado
    request.session["hotel_name"] = hotel.name
    
    add_flash_message(request, "Perfil atualizado com sucesso!", "success")
    return RedirectResponse(url=request.url_for("profile"), status_code=303)
