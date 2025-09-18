from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Form, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.models.guest import Guest
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from validate_docbr import CNPJ
from passlib.hash import bcrypt

from app.core.config import SessionLocal
from app.models.hotel import Hotel
from app.schemas.hotel import HotelCreate, HotelOut, RegisterHotelStep1In, RegisterHotelStep1Out
from app.core.security import generate_csrf_token, validate_csrf_token, hash_password, verify_password, create_access_token, decode_access_token
from app.utils.brdocs import is_valid_cnpj, format_cnpj, only_digits
from app.utils.flash import add_flash_message, render
from app.services.cnpj_ws import fetch_cnpj_situacao, CNPJWsError

router = APIRouter(prefix="/auth", tags=["hotels"])
api_router = APIRouter(prefix="/api", tags=["api_hotels"])
templates = Jinja2Templates(directory="app/templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

@api_router.get("/get_hotels", response_model=List[HotelOut])
def get_hotels(
    cnpj: Optional[str] = Query(None, description="Filtrar pelo CNPJ do hotel"),
    name: Optional[str] = Query(None, description="Filtrar pelo nome do hotel"),
    db: Session = Depends(get_db)
):
    query = db.query(Hotel)

    if cnpj:
        query = query.filter(Hotel.cnpj == cnpj)
    if name:
        query = query.filter(Hotel.name.ilike(f"%{name}%"))

    hotels = query.all()

    if not hotels:
        raise HTTPException(status_code=404, detail="Nenhum hotel encontrado")
    
    return hotels

@router.get("", response_class=HTMLResponse, include_in_schema=False)
def get_registration_form(request: Request):
    csrf_token = generate_csrf_token()
    add_flash_message(request, "teste", "success")
    return render(
        templates,
        request,
        "/auth/register.html",
        {
            "request": request,
            "csrf_token": csrf_token
        }
    )

@router.post("/register/check", response_model=RegisterHotelStep1Out)
async def register_check(request: Request, payload: RegisterHotelStep1In, db: Session = Depends(get_db),):
    email = payload.email
    cnpj = payload.cnpj
    if not is_valid_cnpj(cnpj):
        return RegisterHotelStep1Out(ok=False, message="CNPJ inválido")

    cnpj_digits = only_digits(cnpj)
    query = db.query(Hotel).filter(Hotel.cnpj == cnpj_digits).filter(Hotel.email == email)
    if query.first():
        return RegisterHotelStep1Out(ok=False, message="CNPJ ou email já cadastrado")
    
    request.session["reg_email"] = str(email)
    request.session["reg_cnpj"] = cnpj_digits
    
    return RegisterHotelStep1Out(
        ok=True,
        message="Validação bem-sucedida",
        cnpj=cnpj_digits,
        email=email)

@router.get('/register/step2', response_class=HTMLResponse, include_in_schema=False)
def register_step2_partial(request: Request, email: str, cnpj: str):
    csrf_token = generate_csrf_token()
    email = request.session.get("reg_email")
    cnpj_digits = request.session.get("reg_cnpj")
    if not email or not cnpj_digits:
        add_flash_message(request, "Sessão expirada, tente novamente.", "danger")
        return RedirectResponse(url="/auth/register", status_code=303)
    return templates.TemplateResponse("/auth/partials/register_step2.html", {"request": request, "csrf_token": csrf_token, "email": email, "cnpj": cnpj})


@router.post("/register", response_model=HotelOut)
async def register_hotel(
    request: Request,
    csrf_token: str = Form(...),
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
    if not validate_csrf_token(csrf_token):
        add_flash_message(request, "Token CSRF adulterado, operação finalizada.", "danger")
        return RedirectResponse(url="/auth", status_code=303)
    
    sess_email = request.session.get('reg_email')
    sess_cnpj = request.session.get('reg_cnpj')

    if not sess_email or not sess_cnpj:
        add_flash_message(request, "Sessão expirada.", "danger")
        return RedirectResponse(url="/auth", status_code=303)
    
    cnpj_digits = only_digits(cnpj)
    if str(email).strip().lower() != str(sess_email).strip().lower() or cnpj_digits != sess_cnpj:
        add_flash_message(request, "Dados não foram validados, adulteração detectada.", "danger")
        return RedirectResponse(url="/auth", status_code=303)
    
    if not is_valid_cnpj(cnpj):
        add_flash_message(request, "CNPJ Inválido", "danger")
        return RedirectResponse(url="/auth", status_code=303)

    db_hotel = db.query(Hotel).filter(Hotel.cnpj == cnpj).first()
    if db_hotel:
        add_flash_message(request, "O hotel já existe em nossos registros")
        return RedirectResponse(url="/auth", status_code=303)

    if password != confirm_password:
        add_flash_message(request, "As senhas não conferem.")
        return RedirectResponse(url="/auth", status_code=303)
    
    try:
        situ = await fetch_cnpj_situacao(cnpj_digits)
    except CNPJWsError as e:
        add_flash_message(request, str(e), "danger")
        return RedirectResponse(url="/auth", status_code=303)
    
    if situ.lower() != "ativa":
        add_flash_message(request, "CNPJ com situação irregular")
        return RedirectResponse(url='/auth', status_code=303)

    hashed_password = bcrypt.hash(password)

    new_hotel = Hotel(
        name=name,
        email=email,
        phone_number=ddd+phone_number,
        cnpj=cnpj,
        login=login,
        address=address + ", " + number,
        city=city,
        state=state,
        zip_code=zip_code,
        password=hashed_password
    )

    db.add(new_hotel)
    db.commit()
    db.refresh(new_hotel)
    return RedirectResponse(url="/", status_code=303)

@router.get("/login", response_class=HTMLResponse, include_in_schema=False)
def get_login_form(request: Request):
    csrf_token = generate_csrf_token()
    return templates.TemplateResponse("/auth/login.html", {"request": request, "csrf_token": csrf_token})

@router.post("/login")
def login(
    request: Request,
    csrf_token: str = Form(...),
    login: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    if validate_csrf_token(csrf_token):
        hotel = db.query(Hotel).filter(Hotel.login == login).first()
        if not hotel:
            hotel = db.query(Hotel).filter(Hotel.cnpj == login).first()
            if not hotel:
                raise HTTPException(status_code=400, detail="Login ou CNPJ não encontrado")
        elif hotel and not verify_password(password, hotel.password):
            raise HTTPException(status_code=400, detail="Senha incorreta")
    else:
        raise HTTPException(status_code=400, detail="Invalid CSRF token")
    
    request.session['hotel_id'] = hotel.id
    request.session['hotel_name'] = hotel.name

    response = RedirectResponse(url="/dashboard", status_code=302)
    return response

@router.get("/logout", include_in_schema=False)
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/auth/login", status_code=302)
