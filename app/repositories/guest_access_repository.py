from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.guest import Guest
from app.models.reservations import Reservations
from app.models.rooms import Rooms
from app.models.services import Services


class GuestAccessRepository:

    @staticmethod
    def find_guest_by_cpf(db: Session, cpf: str):
        return (
            db.query(Guest)
            .filter(Guest.cpf == cpf)
            .first()
        )

    @staticmethod
    def find_active_reservation(db: Session, reservation_id: int, guest_id: int):
        return (
            db.query(Reservations, Rooms)
            .join(Rooms, Reservations.room_id == Rooms.id)
            .filter(
                Reservations.id == reservation_id,
                Reservations.guest_id == guest_id,
                Reservations.status == 'checked_in'
            )
            .first()
        )

    @staticmethod
    def find_reservation_by_id(db: Session, reservation_id: int):
        return (
            db.query(Reservations)
            .filter(Reservations.id == reservation_id)
            .first()
        )

    @staticmethod
    def find_services_by_reservation(db: Session, reservation_id: int):
        return (
            db.query(Services)
            .filter(Services.reservation_id == reservation_id)
            .order_by(desc(Services.created_at))
            .all()
        )

    @staticmethod
    def find_service_by_id(db: Session, service_id: int):
        return (
            db.query(Services)
            .filter(Services.id == service_id)
            .first()
        )

    @staticmethod
    def create_service_request(db: Session, reservation_id: int, guest_id: int, room_id: int, description: str):
        new_request = Services(
            reservation_id=reservation_id,
            guest_id=guest_id,
            room_id=room_id,
            request=description,
            status='pending',
        )
        db.add(new_request)
        db.commit()
        db.refresh(new_request)
        return new_request