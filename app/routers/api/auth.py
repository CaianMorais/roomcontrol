#import de libs built-in
from typing import List, Optional

# import de libs third-party
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

#import do current-app
from app.core.config import get_db
from app.core.dependencies import get_api_access
from app.schemas.rooms import HotelOut
from app.services.auth_hotel_service import ApiAuthHotelService

api_router = APIRouter(
    prefix="/api",
    tags=["hotels"],
    dependencies=[Depends(get_api_access)]
)

############## API (ENDPOINTS) ################

@api_router.get("/hotels", response_model=List[HotelOut], summary="Filtrar hotéis (Exclusivo para chave global)")
def get_hotels(
    access: dict = Depends(get_api_access),
    cnpj: Optional[str] = Query(None, description="Filtrar pelo CNPJ do hotel"),
    name: Optional[str] = Query(None, description="Filtrar pelo nome do hotel"),
    db: Session = Depends(get_db)
):
    if not access["is_global"]:
        raise HTTPException(status_code=403, detail="API Key não autorizada")

    hotels = ApiAuthHotelService.list_hotels(db, cnpj, name)

    if not hotels:
        hotels = []

    return hotels