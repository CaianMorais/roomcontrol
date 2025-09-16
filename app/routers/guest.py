from fastapi import FastAPI, HTTPException, Request, Form, Depends, APIRouter
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from validate_docbr import CPF
from fastapi.templating import Jinja2Templates

from app.core.config import SessionLocal
from app.schemas.guest import GuestCreate, GuestOut
from app.models.guest import Guest
from app.core.security import validate_csrf_token, generate_csrf_token

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(tags=["Guests"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=GuestOut)
def create_guest(guest: GuestCreate, db: Session = Depends(get_db)):
    db_guest = Guest(name=guest.name,
                    email=guest.email,
                    phone_number=guest.phone_number,
                    cpf=guest.cpf)
    db.add(db_guest)
    db.commit()
    db.refresh(db_guest)
    return db_guest

# @router.get("/", response_model=list[GuestOut])
# def read_guests(db: Session = Depends(get_db)) -> list[Guest]:
#     return db.query(Guest).all()

@router.get("/guests/new", response_class=HTMLResponse)
def new_guest_form(request: Request):
    csrf_token = generate_csrf_token()
    return templates.TemplateResponse("guest_form.html", {"request": request, "csrf_token": csrf_token})

@router.post("/guests/new")
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