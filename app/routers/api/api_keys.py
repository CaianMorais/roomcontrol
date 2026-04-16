# import de libs third-party
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

#import do current-app
from app.core.config import get_db
from app.core.dependencies import get_api_access
from app.services.api_key_service import ApiKeyService


# configuração do router
api_router = APIRouter(
    prefix="/api",
    tags=["api_keys"],
    dependencies=[Depends(get_api_access)]
)

############## API (ENDPOINTS) ################
# ENDPOINT PRÉ EXISTENTE PARA CASO FUTURO
@api_router.get("/keys")
def get_api_keys(
    db: Session = Depends(get_db)
):
    logs = ApiKeyService.list_keys(db)

    if not logs:
        logs = []

    return logs