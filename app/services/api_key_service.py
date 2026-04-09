import hashlib
import secrets

from sqlalchemy.orm import Session

from app.repositories.api_key_repository import ApiKeyRepository


class ApiKeyService:

    @staticmethod
    def _generate_raw_key() -> str:
        return f"rc_{secrets.token_urlsafe(32)}"

    @staticmethod
    def _hash_key(raw_key: str) -> str:
        return hashlib.sha256(raw_key.encode()).hexdigest()

    @staticmethod
    def validate_key(db: Session, raw_key: str):
        key_hash = ApiKeyService._hash_key(raw_key)
        api_key = ApiKeyRepository.find_by_hash(db, key_hash)
        if not api_key:
            return None
        ApiKeyRepository.update_last_used(db, api_key)
        return api_key

    @staticmethod
    def list_keys(db: Session, hotel_id: int):
        return ApiKeyRepository.get_by_hotel(db, hotel_id)

    @staticmethod
    def create_key(db: Session, hotel_id: int, name: str):
        raw_key = ApiKeyService._generate_raw_key()
        key_hash = ApiKeyService._hash_key(raw_key)

        api_key, error = ApiKeyRepository.create(db, hotel_id, name, key_hash)
        if error:
            return None, None, error

        return api_key, raw_key, None

    @staticmethod
    def toggle_key(db: Session, api_key_id: int, hotel_id: int):
        api_key = ApiKeyRepository.find_by_id(db, api_key_id, hotel_id)
        if not api_key:
            return None, "A chave não foi encontrada."

        api_key, error = ApiKeyRepository.toggle_active(db, api_key)
        if error:
            return None, error

        return api_key, None