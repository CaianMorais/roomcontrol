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
from app.schemas.hotel import HotelCreate, HotelOut
from app.core.security import generate_csrf_token, validate_csrf_token, hash_password, verify_password, create_access_token, decode_access_token

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

@router.get("/register", response_class=HTMLResponse, include_in_schema=False)
def get_registration_form(request: Request):
    csrf_token = generate_csrf_token()
    return templates.TemplateResponse("/auth/register.html", {"request": request, "csrf_token": csrf_token})

@router.post("/register", response_model=HotelOut)
def register_hotel(
    request: Request,
    csrf_token: str = Form(...),
    name: str = Form(...),
    email: str = Form(...),
    phone_number: str = Form(...),
    cnpj: str = Form(...),
    login: str = Form(...),
    address: str = Form(...),
    city: str = Form(...),
    state: str = Form(...),
    zip_code: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db),
):
    if not validate_csrf_token(csrf_token):
        raise HTTPException(status_code=400, detail="Invalid CSRF token")

    db_hotel = db.query(Hotel).filter(Hotel.cnpj == cnpj).first()
    if db_hotel:
        raise HTTPException(status_code=400, detail="Hotel already registered")
    
    # if not CNPJ().validate(hotel.cnpj):
    #     raise HTTPException(status_code=400, detail="Invalid CNPJ")

    if password != confirm_password:
        return {"error": "As senhas não conferem"}

    hashed_password = bcrypt.hash(password)

    
    new_hotel = Hotel(
        name=name,
        email=email,
        phone_number=phone_number,
        cnpj=cnpj,
        login=login,
        address=address,
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
