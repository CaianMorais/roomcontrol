# import de libs third-party
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

# import do current-app
from app.core.config import get_db
from app.core.security import generate_csrf_token, validate_csrf_token
from app.repositories.auth_hotel_repository import HotelRepository
from app.schemas.hotel import HotelOut, RegisterHotelStep1In, RegisterHotelStep1Out
from app.services.auth_collaborator_service import AuthCollaboratorService
from app.services.auth_hotel_service import AuthHotelService
from app.utils.flash import add_flash_message, render

router = APIRouter(
    prefix="/auth",
    tags=["hotels"]
)

templates = Jinja2Templates(directory="app/templates")

################### REGISTRO DE HOTEL #################

@router.get("/hotel", response_class=HTMLResponse, include_in_schema=False)
def get_registration_form(request: Request):
    if request.session.get("collaborator_id") or request.session.get("hotel_id"):
        return RedirectResponse(url=request.url_for("dashboard"), status_code=303)

    csrf_token = generate_csrf_token(request)
    return render(
        templates,
        request,
        "/auth/register.html",
        {"csrf_token": csrf_token}
    )


@router.post("/register/check", response_model=RegisterHotelStep1Out, include_in_schema=False)
async def register_check(
    request: Request,
    payload: RegisterHotelStep1In,
    db: Session = Depends(get_db),
):
    cnpj_digits, error = AuthHotelService.check_registration(db, str(payload.email), payload.cnpj)

    if error:
        return RegisterHotelStep1Out(ok=False, message=error)

    request.session["reg_email"] = str(payload.email)
    request.session["reg_cnpj"] = cnpj_digits

    return RegisterHotelStep1Out(
        ok=True,
        message="Validação bem-sucedida",
        cnpj=cnpj_digits,
        email=payload.email
    )


@router.get("/register/step2", response_class=HTMLResponse, include_in_schema=False)
def register_step2_partial(request: Request, email: str, cnpj: str):
    email = request.session.get("reg_email")
    cnpj_digits = request.session.get("reg_cnpj")

    if not email or not cnpj_digits:
        add_flash_message(request, "Sessão expirada, tente novamente.", "danger")
        return RedirectResponse(url=request.url_for("get_registration_form"), status_code=303)

    csrf_token = generate_csrf_token(request)
    return templates.TemplateResponse(
        "/auth/partials/register_step2.html",
        {
            "request": request,
            "csrf_token": csrf_token,
            "email": email,
            "cnpj": cnpj_digits
        }
    )


@router.post("/register", response_model=HotelOut, include_in_schema=False)
async def register_hotel(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    ddd: str = Form(...),
    phone_number: str = Form(...),
    cnpj: str = Form(...),
    login: str = Form(...),
    address: str = Form(...),
    number: str = Form(...),
    city: str = Form(...),
    state: str = Form(...),
    zip_code: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db),
):
    form = await request.form()
    csrf_token = form.get("csrf_token") or request.headers.get("X-CSRF-Token")
    if not validate_csrf_token(request, csrf_token):
        add_flash_message(request, "Token de segurança inválido, operação finalizada.", "danger")
        return RedirectResponse(url=request.url_for("get_registration_form"), status_code=303)

    sess_email = request.session.get("reg_email")
    sess_cnpj = request.session.get("reg_cnpj")

    if not sess_email or not sess_cnpj:
        add_flash_message(request, "Sessão expirada.", "danger")
        return RedirectResponse(url=request.url_for("get_registration_form"), status_code=303)

    hotel, error = await AuthHotelService.register(
        db=db,
        sess_email=sess_email,
        sess_cnpj=sess_cnpj,
        email=email,
        cnpj=cnpj,
        name=name,
        login=login,
        ddd=ddd,
        phone_number=phone_number,
        address=address,
        number=number,
        city=city,
        state=state,
        zip_code=zip_code,
        password=password,
        confirm_password=confirm_password,
    )

    if error:
        add_flash_message(request, error, "danger")
        return RedirectResponse(url=request.url_for("get_registration_form"), status_code=303)

    request.session.pop("reg_email", None)
    request.session.pop("reg_cnpj", None)
    add_flash_message(request, "Hotel cadastrado com sucesso!", "success")
    return RedirectResponse(url=request.url_for("get_registration_form"), status_code=303)


############## LOGIN E LOGOUT DE HOTEL #################

@router.post("/login", include_in_schema=False)
async def login(
    request: Request,
    login: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    form = await request.form()
    csrf_token = form.get("csrf_token")

    if not validate_csrf_token(request, csrf_token):
        add_flash_message(request, "Token de segurança inválido, tente novamente", "warning")
        return RedirectResponse(url=request.url_for("get_registration_form"), status_code=303)

    hotel, error = AuthHotelService.login(db, login, password)

    if error:
        add_flash_message(request, error, "warning")
        return RedirectResponse(url=request.url_for("get_registration_form"), status_code=303)

    request.session.clear()
    request.session["hotel_id"] = hotel.id
    request.session["hotel_name"] = hotel.name
    request.session['admin_logged_in'] = True

    add_flash_message(request, "Login bem-sucedido!", "success")
    return RedirectResponse(url=request.url_for("dashboard"), status_code=302)


@router.get("/logout", include_in_schema=False)
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url=request.url_for("home"), status_code=303)


#################### LOGIN DE COLABORADOR ########################

@router.get("/collaborator", response_class=HTMLResponse, include_in_schema=False)
def auth_collaborator(request: Request, db: Session = Depends(get_db)):
    if request.session.get("collaborator_id") or request.session.get("hotel_id"):
        return RedirectResponse(url=request.url_for("dashboard"), status_code=303)

    hotels = HotelRepository.find_all_active(db)
    csrf_token = generate_csrf_token(request)

    return render(
        templates,
        request,
        "/auth/collaborator_login.html",
        {
            "hotels": hotels,
            "csrf_token": csrf_token
        }
    )


@router.post("/collaborator", response_class=HTMLResponse, include_in_schema=False)
def login_collaborator(
    request: Request,
    csrf_token: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    hotel: int = Form(...),
    db: Session = Depends(get_db)
):
    if not validate_csrf_token(request, csrf_token):
        add_flash_message(request, "Token de segurança inválido, tente novamente", "danger")
        return RedirectResponse(url=request.url_for("login_collaborator"), status_code=303)
    
    collaborator, needs_password_change, error = AuthCollaboratorService.login(db, username, password, hotel)

    if error:
        add_flash_message(request, error, "danger")
        return RedirectResponse(url=request.url_for("login_collaborator"), status_code=303)

    request.session.clear()
    request.session["hotel_id"] = collaborator.hotel_id
    request.session["hotel_name"] = collaborator.hotel.name
    request.session["collaborator_id"] = collaborator.id
    request.session["collaborator_name"] = collaborator.firstname + " " + collaborator.lastname

    if needs_password_change:
        request.session["force_change_password"] = True
        add_flash_message(request, "Redefinição de senha necessária", "info")
        return RedirectResponse(url=request.url_for("change_password_page"), status_code=303)

    return RedirectResponse(url=request.url_for("dashboard"), status_code=303)


@router.get("/collaborator/change_password", response_class=HTMLResponse, include_in_schema=False)
def change_password_page(request: Request):
    if not request.session.get("force_change_password"):
        return RedirectResponse(url=request.url_for("dashboard"), status_code=303)

    return render(
        templates,
        request,
        "auth/collaborator_change_password.html",
        {
            "csrf_token": generate_csrf_token(request)
        }
    )


@router.post("/collaborator/change_password", response_class=HTMLResponse, include_in_schema=False)
def change_password(
    request: Request,
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    csrf_token: str = Form(...),
    db: Session = Depends(get_db)
):
    if not validate_csrf_token(request, csrf_token):
        add_flash_message(request, "Token de segurança inválido, operação finalizada.", "danger")
        return RedirectResponse(url=request.url_for("change_password_page"), status_code=303)

    collaborator_id = request.session.get("collaborator_id")

    collaborator, error = AuthCollaboratorService.change_password(
        db, collaborator_id, new_password, confirm_password
    )

    if error:
        add_flash_message(request, error, "danger")
        return RedirectResponse(url=request.url_for("change_password_page"), status_code=303)

    request.session.pop("force_change_password", None)
    add_flash_message(request, "Senha alterada com sucesso", "success")
    return RedirectResponse(url=request.url_for("dashboard"), status_code=303)