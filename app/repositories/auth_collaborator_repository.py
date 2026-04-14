from sqlalchemy.orm import Session

from app.models.collaborator import Collaborator


class CollaboratorAuthRepository:

    @staticmethod
    def find_active_by_username_and_hotel(db: Session, username: str, hotel_id: int):
        return (
            db.query(Collaborator)
            .filter(
                Collaborator.username == username,
                Collaborator.hotel_id == hotel_id,
                Collaborator.is_active == True,
                Collaborator.is_deleted == False,
            )
            .first()
        )

    @staticmethod
    def find_active_by_id(db: Session, collaborator_id: int):
        return (
            db.query(Collaborator)
            .filter(
                Collaborator.id == collaborator_id,
                Collaborator.is_active == True,
                Collaborator.is_deleted == False,
            )
            .first()
        )

    @staticmethod
    def update_password(db: Session, collaborator: Collaborator, hashed_password: str):
        collaborator.password = hashed_password
        collaborator.change_password = False
        db.commit()