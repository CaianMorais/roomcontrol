# import de libs padrao
from typing import List, Optional

#import de libs third-party

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

# import de funções da aplicação local

from app.core.config import get_db
from app.core.dependencies import get_api_access
from app.schemas.guest import GuestOut
from app.services.guest_service import ApiGuestService

api_router = APIRouter(
    prefix="/api",
    tags=["guests"],
    dependencies=[Depends(get_api_access)]
)

@api_router.get("/guests", response_model=List[GuestOut], summary="Filtrar hóspedes")
def get_guests(
    access: dict = Depends(get_api_access),
    guest_cpf: Optional[str] = Query(None, description="Filtrar pelo CPF do hóspede"),
    guest_name: Optional[str] = Query(None, description="Filtrar pelo nome do hóspede"),
    hotel_id: Optional[str] = Query(None, description="Filtrar pelo ID do hotel (FUNCIONAL SOMENTE PARA CHAVE GLOBAL)"),
    hotel_name: Optional[str] = Query(None, description="Filtrar pelo nome do hotel (FUNCIONAL SOMENTE PARA CHAVE GLOBAL)"),
    db: Session = Depends(get_db)
):

    # Se o acesso não é global, salva o hotel_id relacionado a chave
    if not access["is_global"]:
        query = ApiGuestService.get_guests(db, access["hotel_id"])

    else:
        query = ApiGuestService.get_guests(db, None)
        if hotel_id or hotel_name:
            print(hotel_id, hotel_name)
            query = ApiGuestService.filter_guests(query, hotel_id=hotel_id, hotel_name=hotel_name)

    if guest_cpf or guest_name:
        query = ApiGuestService.filter_guests(query, name=guest_name, cpf=guest_cpf)

    guests = query.all()

    if not guests:
        guests = []

    return guests