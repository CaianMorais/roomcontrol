from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query, Request, Form, Depends, APIRouter
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from validate_docbr import CPF
from fastapi.templating import Jinja2Templates

from app.core.config import SessionLocal
from app.schemas.guest import GuestCreate, GuestOut
from app.models.guest import Guest
from app.core.security import validate_csrf_token, generate_csrf_token

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(prefix="/guests", tags=["guests"])
api_router = APIRouter(prefix="/api", tags=["api_guests"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@api_router.get("/get_guests", response_model=List[GuestOut])
def get_guests(
    cpf: Optional[str] = Query(None, description="Filtrar pelo CPF do hóspede"),
    name: Optional[str] = Query(None, description="Filtrar pelo nome do hóspede"),
    db: Session = Depends(get_db)
):
    query = db.query(Guest)
    
    if cpf:
        query = query.filter(Guest.cpf == cpf)
    if name:
        query = query.filter(Guest.name.ilike(f"%{name}%"))
    
    guests = query.all()
    
    if not guests:
        raise HTTPException(status_code=404, detail="Nenhum hóspede encontrado")
    
    return guests

@router.get("/new", response_class=HTMLResponse, include_in_schema=False)
def new_guest_form(request: Request):
    csrf_token = generate_csrf_token()
    return templates.TemplateResponse("guest_form.html", {"request": request, "csrf_token": csrf_token})

@router.post("/new")
def create_guest(
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    cpf: str = Form(...),
    csrf_token: str = Form(...),
    db: Session = Depends(get_db)
):
    if not validate_csrf_token(csrf_token):
        raise HTTPException(status_code=400, detail="Invalid CSRF token")

    if not CPF().validate(cpf):
        raise HTTPException(status_code=400, detail="Invalid CPF")

    guest = Guest(name=name, email=email, phone_number=phone, cpf=cpf)
    db.add(guest)
    db.commit()
    db.refresh(guest)
    return RedirectResponse(url="/", status_code=303)