from fastapi import Security, HTTPException, Depends
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.orm import Session
from datetime import datetime
import os

from app.core.config import get_db
from app.core.api_keys import hash_api_key
from app.models.api_keys import ApiKey

# pega a chave da api no header da requisição
api_key_header = APIKeyHeader(
    name="API-KEY",
    auto_error=False
)

def get_api_hotel(
    api_key: str = Security(api_key_header),
    db: Session = Depends(get_db)
) -> int:
    # valida a existÊncia da key
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API Key ausente"
        )

    # gera o hash da key recebida no header
    key_hash = hash_api_key(api_key)

    # consulta a key hashificada
    api_key_db = (
        db.query(ApiKey)
        .filter(
            ApiKey.key_hash == key_hash,
            ApiKey.is_active == True
        )
        .first()
    )

    # valida que existe no banco
    if not api_key_db:
        raise HTTPException(
            status_code=403,
            detail="API Key inválida"
        )

    # atualiza último uso
    api_key_db.last_used_at = datetime.now()
    db.commit()

    # retorna o id do hotel
    return api_key_db.hotel_id



# FUNÇÃO GENÉRICA PARA VERIFICAR
# CHAVE DE API DE NIVEL GLOBAL
# CONFIGURADO NO .env
def get_api_access(
    api_key: str = Security(api_key_header),
    db: Session = Depends(get_db)
):
    if not api_key:
        raise HTTPException(status_code=401, detail="API Key ausente")
    
    # Verifica chave global
    if api_key == os.getenv("GLOBAL_API_KEY"):
        return {
            "is_global": True,
            "hotel_id": None
        }

    key_hash = hash_api_key(api_key)

    api_key_db = (
        db.query(ApiKey)
        .filter(
            ApiKey.key_hash == key_hash,
            ApiKey.is_active == True
        )
        .first()
    )

    if not api_key_db:
        raise HTTPException(status_code=403, detail="API Key inválida")

    api_key_db.last_used_at = datetime.now()
    db.commit()

    return {
        "is_global": False,
        "hotel_id": api_key_db.hotel_id
    }