from app.core.config import SessionLocal
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Form, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from passlib.hash import bcrypt

from app.utils.flash import render
from app.utils.session_guard import require_session
from app.schemas.rooms import RoomOut, RoomCreate, RoomsBase
from app.models.rooms import Rooms

router = APIRouter(
    prefix="/dashboard/rooms",
    tags=["rooms"],
    dependencies=[Depends(require_session)]
)

api_router = APIRouter(prefix="/api", tags=["api_rooms"])
templates = Jinja2Templates(directory="app/templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@api_router.get("/get_rooms", response_model=List[RoomOut])
def get_rooms(
    hotel_id: Optional[str] = Query(None, description="Filtrar pelo ID do hotel"),
    db: Session = Depends(get_db)
):
    query = db.query(Rooms)

    if hotel_id:
        query = query.filter(Rooms.hotel_id == hotel_id)

    rooms = query.all()

    if not rooms:
        raise HTTPException(status_code=404, detail="Nenhum quarto encontrado")
    
    return rooms

@router.get("", response_class=HTMLResponse, include_in_schema=False)
def rooms(request: Request, db: Session = Depends(get_db)):
    rooms = db.query(Rooms).filter_by(hotel_id=request.session.get("hotel_id")).order_by(Rooms.number).all()
    return render(templates, request, "dashboard/rooms.html", {"rooms": rooms})