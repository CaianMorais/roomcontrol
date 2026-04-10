from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models.collaborator import Collaborator
from app.models.hotel import Hotel


class CollaboratorRepository:

    @staticmethod
    def base_query(db: Session, hotel_id: int):
        return (
            db.query(Collaborator)
            .filter(
                Collaborator.hotel_id == hotel_id,
                Collaborator.is_deleted == False
            )
            .order_by(Collaborator.is_active)
            .order_by(Collaborator.created_at.desc())
        )

    @staticmethod
    def find_by_cpf(db: Session, cpf: str, hotel_id: int):
        return (
            db.query(Collaborator)
            .filter(
                Collaborator.cpf == cpf,
                Collaborator.hotel_id == hotel_id
            )
            .first()
        )

    @staticmethod
    def find_by_id(db: Session, collaborator_id: int, hotel_id: int):
        return (
            db.query(Collaborator)
            .filter(
                Collaborator.id == collaborator_id,
                Collaborator.hotel_id == hotel_id,
                Collaborator.is_deleted == False
            )
            .first()
        )

    @staticmethod
    def find_all_global(db: Session):
        return (
            db.query(Collaborator)
            .options(joinedload(Collaborator.hotel))
            .filter(Collaborator.is_deleted == False)
        )

    @staticmethod
    def apply_filters(query, search: str = None, status: str = None):
        if search:
            query = query.filter(
                or_(
                    Collaborator.cpf.ilike(f"%{search}%"),
                    Collaborator.firstname.ilike(f"%{search}%"),
                    Collaborator.lastname.ilike(f"%{search}%")
                )
            )
        if status == "active":
            query = query.filter(Collaborator.is_active == True)
        elif status == "inactive":
            query = query.filter(Collaborator.is_active == False)
        return query

    @staticmethod
    def apply_global_filters(query, hotel_name: str = None, firstname: str = None, lastname: str = None, cpf: str = None):
        if hotel_name:
            query = query.join(Hotel, Collaborator.hotel_id == Hotel.id).filter(Hotel.name.ilike(f"%{hotel_name}%"))
        if firstname:
            query = query.filter(Collaborator.firstname.ilike(f"%{firstname}%"))
        if lastname:
            query = query.filter(Collaborator.lastname.ilike(f"%{lastname}%"))
        if cpf:
            query = query.filter(Collaborator.cpf.ilike(f"%{cpf}%"))
        return query

    @staticmethod
    def create(db: Session, collaborator: Collaborator):
        db.add(collaborator)
        db.commit()
        db.refresh(collaborator)
        return collaborator

    @staticmethod
    def update(db: Session, collaborator: Collaborator):
        db.commit()
        db.refresh(collaborator)
        return collaborator

    @staticmethod
    def soft_delete(db: Session, collaborator: Collaborator):
        collaborator.is_deleted = True
        db.commit()
        return collaborator