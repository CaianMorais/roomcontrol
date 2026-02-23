import secrets
import hashlib
from app.models.api_keys import ApiKey
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

def generate_api_key() -> str:
    return f"rc_{secrets.token_urlsafe(32)}"

def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()

def create_key(db, hotel_id, name, key_hash):
    api_key = ApiKey(
        hotel_id=hotel_id,
        name=name,
        key_hash=key_hash
    )

    try:
        db.add(api_key)
        db.commit()
        db.refresh(api_key)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Erro ao gerar API Key. Tente novamente."
        )