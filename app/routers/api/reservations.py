from typing import List, Optional

# import de libs da third-party
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session, joinedload

# import de funções da aplicação local
from app.core.config import get_db
from app.models.rooms import Rooms
from app.schemas.reservations import ReservationOut
from app.models.reservations import Reservations
from app.models.guest import Guest
from app.models.hotel import Hotel
from app.core.dependencies import get_api_access
from app.services.reservation_service import ApiReservationService

# configuração do router
api_router = APIRouter(
    prefix="/api",
    tags=["reservations"],
    dependencies=[Depends(get_api_access)]
)

@api_router.get("/reservations", response_model=List[ReservationOut], summary="Filtrar reservas")
def get_reservations(
    access: dict = Depends(get_api_access),
    guest_id: Optional[int] = Query(None, description="Filtrar pelo ID do hóspede"),
    guest_name: Optional[str] = Query(None, description="Filtrar pelo nome do hóspede"),
    room_number: Optional[str] = Query(None, description="Filtrar pelo número do quarto"),
    check_in: Optional[str] = Query(None, description="Filtrar pela data de check-in"),
    check_out: Optional[str] = Query(None, description="Filtrar pela data de check-out"),
    hotel_id: Optional[int] = Query(None, description="Filtrar pelo ID do hotel (FUNCIONAL SOMENTE PARA CHAVE GLOBAL)"),
    hotel_name: Optional[str] = Query(None, description="Filtrar pelo nome do hotel (FUNCIONAL SOMENTE PARA CHAVE GLOBAL)"),
    db: Session = Depends(get_db)
):
    # se a chave nao for global, consulta somente do hotel relacionado a chave
    if not access["is_global"]:
        query = ApiReservationService.get_reservations_hotel(db, access["hotel_id"])
    else:
        query = ApiReservationService.get_reservations_global(db)
        if hotel_id or hotel_name:
            query = ApiReservationService.filter_reservations(
                query=query,
                hotel_id=hotel_id,
                hotel_name=hotel_name
            )

    if guest_id or guest_name or room_number or check_in or check_out:
        query = ApiReservationService.filter_reservations(
            query=query,
            guest_id=guest_id,
            guest_name=guest_name,
            room_number=room_number,
            check_in=check_in,
            check_out=check_out
        )

    reservations = query.all()

    if not reservations:
        reservations = []

    return reservations