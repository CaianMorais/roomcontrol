from sqlalchemy.orm import Session
from app.models.guest import Guest
from app.models.reservations import Reservations
from app.models.rooms import Rooms

class GuestRepository:

    @staticmethod
    def base_query(db: Session, hotel_id: int):
        return (
            db.query(Guest)
            .filter(
                Guest.hotel_id == hotel_id,
                Guest.is_deleted == False
            )
        )
    
    @staticmethod
    def _active_reservations_subquery(db: Session):
        # consulta as reservas ativas no hotel
        return (
            db.query(
                Reservations.guest_id,
                Reservations.check_in.label("reservation_check_in"),
                Reservations.status.label("reservation_status"),
                Reservations.id.label("reservation_id"),
                Rooms.room_number.label("room_number")
            )
            .join(Rooms, Rooms.id == Reservations.room_id)
            .filter(
                Reservations.status.in_(["booked", "checked_in"])
            )
            .order_by(Reservations.check_in)
            .subquery()
        )

    @staticmethod
    def guests_with_active_reservations(db: Session, hotel_id: int):
        subquery = GuestRepository._active_reservations_subquery(db)

        # com as reservas ativas armazenadas em "subquery"
        # consulta os hospedes do hotel
        # e anexa a reserva ativa correspondente a ele

        return (
            db.query(
                Guest,
                subquery.c.reservation_check_in,
                subquery.c.reservation_status,
                subquery.c.reservation_id,
                subquery.c.room_number
            )
            .outerjoin(
                subquery,
                Guest.id == subquery.c.guest_id
            )
            .filter(
                Guest.hotel_id == hotel_id,
                Guest.is_deleted == False
            )
        )
    
    @staticmethod
    def filter_guests_by_name_or_cpf(db: Session, name: str , cpf: str, query):
        if name:
            query = query.filter(Guest.name.ilike(f"%{name}%"))
        if cpf:
            query = query.filter(Guest.cpf.like(f"%{cpf}%"))
        return query
    
    @staticmethod
    def find_by_cpf(db: Session, cpf: str, hotel_id: int):
        return (
            db.query(Guest)
            .filter(
                Guest.cpf == cpf,
                Guest.hotel_id == hotel_id
            )
            .first()
        )

    @staticmethod
    def find_by_id(db: Session, guest_id: int, hotel_id: int):
        return (
            db.query(Guest)
            .filter(
                Guest.id == guest_id,
                Guest.hotel_id == hotel_id
            )
            .first()
        )
        
    @staticmethod
    def create(db: Session, guest: Guest):
        db.add(guest)
        db.commit()
        db.refresh(guest)
        return guest
    
    @staticmethod
    def update(db: Session, guest: Guest):
        db.commit()
        db.refresh(guest)
        return guest

    @staticmethod
    def soft_delete(db: Session, guest: Guest):
        guest.is_deleted = True
        db.commit()