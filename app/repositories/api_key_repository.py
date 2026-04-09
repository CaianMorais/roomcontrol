from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.api_keys import ApiKey


class ApiKeyRepository:

    @staticmethod
    def get_by_hotel(db: Session, hotel_id: int):
        return (
            db.query(ApiKey)
            .filter(ApiKey.hotel_id == hotel_id)
            .order_by(ApiKey.is_active.desc())
            .order_by(ApiKey.created_at.desc())
        )

    @staticmethod
    def find_by_id(db: Session, api_key_id: int, hotel_id: int):
        return (
            db.query(ApiKey)
            .filter(
                ApiKey.id == api_key_id,
                ApiKey.hotel_id == hotel_id
            )
            .first()
        )

    @staticmethod
    def create(db: Session, hotel_id: int, name: str, key_hash: str):
        api_key = ApiKey(
            hotel_id=hotel_id,
            name=name,
            key_hash=key_hash
        )
        try:
            db.add(api_key)
            db.commit()
            db.refresh(api_key)
            return api_key, None
        except IntegrityError:
            db.rollback()
            return None, "Erro ao gerar API Key. Tente novamente."

    @staticmethod
    def find_by_hash(db: Session, key_hash: str):
        return (
            db.query(ApiKey)
            .filter(
                ApiKey.key_hash == key_hash,
                ApiKey.is_active == True
            )
            .first()
        )

    @staticmethod
    def update_last_used(db: Session, api_key: ApiKey):
        from datetime import datetime
        api_key.last_used_at = datetime.now()
        db.commit()

    @staticmethod
    def toggle_active(db: Session, api_key: ApiKey):
        try:
            api_key.is_active = not api_key.is_active
            db.commit()
            db.refresh(api_key)
            return api_key, None
        except IntegrityError:
            db.rollback()
            return None, "Erro ao atualizar o status da chave."