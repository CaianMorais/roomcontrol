from fastapi import Security, HTTPException, Depends
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.config import get_db
from app.core.api_keys import hash_api_key
from app.models.api_keys import ApiKey

api_key_header = APIKeyHeader(
    name="X-API-KEY",
    auto_error=False
)

def get_api_hotel(
    api_key: str = Security(api_key_header),
    db: Session = Depends(get_db)
) -> int:
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API Key ausente"
        )

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
        raise HTTPException(
            status_code=403,
            detail="API Key inválida"
        )

    # Atualiza último uso
    api_key_db.last_used_at = datetime.now()
    db.commit()

    return api_key_db.hotel_id