from fastapi import Security, HTTPException, Depends
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.orm import Session
import os

from app.core.config import get_db
from app.services.api_key_service import ApiKeyService

# pega a chave da api no header da requisição
api_key_header = APIKeyHeader(
    name="API-KEY",
    auto_error=False
)

# def get_api_hotel(
#     api_key: str = Security(api_key_header),
#     db: Session = Depends(get_db)
# ) -> int:
#     # valida a existÊncia da key
#     if not api_key:
#         raise HTTPException(
#             status_code=401,
#             detail="API Key ausente."
#         )

#     # valida a chave da API
#     api_key_db = ApiKeyService.validate_key(db, api_key)

#     # valida que existe no banco
#     if not api_key_db:
#         raise HTTPException(status_code=403, detail="API Key bloqueada ou inválida.")

#     # retorna o id do hotel
#     return api_key_db.hotel_id



# FUNÇÃO GENÉRICA PARA VERIFICAR
# CHAVE DE API DE NIVEL GLOBAL
# CONFIGURADO NO .env
def get_api_access(
    api_key: str = Security(api_key_header),
    db: Session = Depends(get_db)
):
    if not api_key:
        raise HTTPException(status_code=401, detail="API Key ausente.")
    
    # Verifica chave global
    if api_key == os.getenv("GLOBAL_API_KEY"):
        return {
            "is_global": True,
            "hotel_id": None
        }

    api_key_db = ApiKeyService.validate_key(db, api_key)

    if not api_key_db:
        raise HTTPException(status_code=403, detail="API Key bloqueada ou inválida.")

    return {
        "is_global": False,
        "hotel_id": api_key_db.hotel_id
    }