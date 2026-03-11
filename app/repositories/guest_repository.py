from sqlalchemy import func
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
    def _active_reservations_subquery(db: Session, hotel_id: int):
        # consulta as reservas ativas no hotel
        return db.query(
                Reservations.guest_id,
                Reservations.check_in.label("reservation_check_in"),
                Reservations.status.label("reservation_status"),
                Reservations.id.label("reservation_id"),
                Rooms.room_number.label("room_number"),
                # numera as reservas de cada hospede:
                func.row_number().over(
                    # agrupa por ID do hospede:
                    partition_by=Reservations.guest_id,
                    #ordena por data de check-in mais recente:
                    order_by=Reservations.check_in.asc()
                ).label("rn")
            ) \
            .join(Rooms, Rooms.id == Reservations.room_id) \
            .filter(
                Reservations.status.in_(["booked", "checked_in"]),
                Rooms.hotel_id == hotel_id
            ) \
            .order_by(Reservations.check_in) \
            .subquery()

    @staticmethod
    def guests_with_active_reservations(db: Session, hotel_id: int):
        subquery = GuestRepository._active_reservations_subquery(db, hotel_id)

        # com as reservas ativas armazenadas em "subquery"
        # consulta os hospedes do hotel
        # e anexa a reserva ativa correspondente a ele

        query = db.query(
                Guest,
                subquery.c.reservation_check_in,
                subquery.c.reservation_status,
                subquery.c.reservation_id,
                subquery.c.room_number
            ) \
            .outerjoin(
                subquery,
                (Guest.id == subquery.c.guest_id) & (subquery.c.rn == 1) # pega somente a reserva mais recente de cada hospede
            ) \
            .filter(
                Guest.hotel_id == hotel_id,
                Guest.is_deleted == False
            )
                
        return query
    
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
                Guest.hotel_id == hotel_id,
                Guest.is_deleted == False
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
        reservations = db.query(Reservations) \
        .filter(Reservations.guest_id == guest.id) \
        .filter(Reservations.status.in_(["booked", "checked_in"])) \
        .all()

        for reservation in reservations:
            if reservation.status == "checked_in":
                rooms = db.query(Rooms) \
                .filter(Rooms.id == reservation.room_id) \
                .filter(Rooms.status == 'occupied') \
                .first()
                rooms.status = "available"
            reservation.status = "canceled"

        guest.is_deleted = True
        db.commit()