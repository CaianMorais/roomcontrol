# import de libs built-in
from decimal import Decimal
from typing import List, Optional

# import de libs third-party
from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import paginate as sa_paginate

# import do current-app
from app.core.config import get_db
from app.core.dependencies import get_api_access
from app.core.security import generate_csrf_token, validate_csrf_token
from app.models.hotel import Hotel
from app.models.rooms import Rooms
from app.services.audit_service import AuditService
from app.services.room_service import ApiRoomsService
from app.schemas.rooms import RoomOut
from app.utils.flash import add_flash_message, render
from app.utils.session_guard import require_session

# configurações do router
api_router = APIRouter(
    prefix="/api",
    tags=["rooms"],
    dependencies=[Depends(get_api_access)]
)

internal_api_router = APIRouter(
    prefix="/internal_api",
    tags=["rooms"],
    dependencies=[Depends(require_session)]
)

@api_router.get("/rooms", response_model=List[RoomOut], summary="Filtrar quartos")
def get_rooms(
    access: dict = Depends(get_api_access),
    hotel_name: Optional[str] = Query(None, description="Filtrar pelo nome do hotel (FUNCIONAL SOMENTE PARA CHAVE GLOBAL)"),
    hotel_id: Optional[int] = Query(None, description="Filtrar pelo ID do hotel (FUNCIONAL SOMENTE PARA CHAVE GLOBAL)"),
    db: Session = Depends(get_db)
):

    if not access["is_global"]:
        query = ApiRoomsService.get_rooms(db, hotel_id=access["hotel_id"])

    if access["is_global"]:
        query = ApiRoomsService.get_rooms(db, hotel_id=None)
        if hotel_name or hotel_id:
            query = ApiRoomsService.filter_rooms(query, hotel_name=hotel_name, hotel_id=hotel_id)

    rooms = query.all()

    if not rooms:
        rooms = []
    
    return rooms

@internal_api_router.get("/rooms", include_in_schema=False)
def get_rooms_for_reservations_filter(
    request: Request,
    db: Session = Depends(get_db)
):
    hotel_id = request.session.get("hotel_id")
    if not hotel_id:
        raise HTTPException(status_code=400, detail="Hotel não reconhecido")
    
    rooms = ApiRoomsService.get_rooms(db, hotel_id=hotel_id).all()

    return rooms