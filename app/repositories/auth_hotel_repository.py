from typing import Optional
from sqlalchemy.orm import Session

from app.models.hotel import Hotel
from app.utils.brdocs import only_digits


class HotelRepository:

    @staticmethod
    def base_query(db: Session):
        return db.query(Hotel)

    @staticmethod
    def find_by_cnpj(db: Session, cnpj_digits: str):
        return (
            db.query(Hotel)
            .filter(Hotel.cnpj == cnpj_digits)
            .first()
        )

    @staticmethod
    def find_by_cnpj_and_email(db: Session, cnpj_digits: str, email: str):
        return (
            db.query(Hotel)
            .filter(Hotel.cnpj == cnpj_digits, Hotel.email == email)
            .first()
        )

    @staticmethod
    def find_by_login_or_cnpj(db: Session, login: str):
        hotel = db.query(Hotel).filter(Hotel.login == login).first()
        if not hotel:
            hotel = db.query(Hotel).filter(Hotel.cnpj == only_digits(login)).first()
        return hotel

    @staticmethod
    def find_all_active(db: Session):
        return db.query(Hotel).filter(Hotel.is_active == True).all()

    @staticmethod
    def apply_filters(query, cnpj: Optional[str] = None, name: Optional[str] = None):
        if cnpj:
            query = query.filter(Hotel.cnpj.ilike(f"%{cnpj}%"))
        if name:
            query = query.filter(Hotel.name.ilike(f"%{name}%"))
        return query

    @staticmethod
    def create(db: Session, hotel: Hotel):
        db.add(hotel)
        db.commit()
        db.refresh(hotel)
        return hotel