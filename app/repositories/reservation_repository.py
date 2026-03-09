from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.guest import Guest
from app.models.reservations import Reservations
from app.models.rooms import Rooms
import datetime

class ReservationRepository:

    @staticmethod
    def base_query(db: Session, hotel_id: int):
        return (
            db.query(Reservations, Rooms.is_deleted, Rooms.room_number, Guest.is_deleted, Guest.name, Guest.id)
            .join(Rooms, Rooms.id == Reservations.room_id)
            .join(Guest, Guest.id == Reservations.guest_id)
            .filter(Rooms.hotel_id == hotel_id)
        )
    
    @staticmethod
    def get_reservations(db: Session, hotel_id: int):
        return ReservationRepository.base_query(db, hotel_id)
    
    @staticmethod
    def apply_filters(
        query,
        search=None,
        room=None,
        status=None,
        interval_in=None,
        check_in_dt=None,
        interval_out=None,
        check_out_dt=None
    ):

        if search:
            query = query.filter(
                or_(
                    Reservations.id == search,
                    Guest.name.ilike(f"%{search}%")
                )
            )

        if room:
            query = query.filter(Rooms.id == room)

        if status:
            query = query.filter(Reservations.status == status)

        if interval_in and check_in_dt:
            if interval_in == "before":
                query = query.filter(Reservations.check_in < check_in_dt)
            elif interval_in == "after":
                query = query.filter(Reservations.check_in > check_in_dt)

        if interval_out and check_out_dt:
            if interval_out == "before":
                query = query.filter(Reservations.check_out < check_out_dt)
            elif interval_out == "after":
                query = query.filter(Reservations.check_out > check_out_dt)

        return query

    @staticmethod
    def check_guest_conflict(db, guest_id, check_in, check_out):
        guest_conflict = db.query(Reservations).filter(
            Reservations.status.not_in(["canceled", "checked_out"]),
            Reservations.guest_id == guest_id,
            Reservations.check_in < check_out,
            Reservations.check_out > check_in
        ).first()

        return guest_conflict
    
    @staticmethod
    def check_available_guests(db, hotel_id, check_in, check_out):
        reserved_guest_ids = db.query(Reservations.guest_id).filter(
            Reservations.check_in < check_out,
            Reservations.check_out > check_in,
            Reservations.status.in_(["booked", "checked_in"])
        ).subquery()

        available_guests = db.query(Guest).filter(
            Guest.hotel_id == hotel_id,
            Guest.is_deleted == False,
            ~Guest.id.in_(reserved_guest_ids)
        ).all()

        return available_guests
    
    @staticmethod
    def check_available_rooms(db, hotel_id, check_in, check_out):
        # Pega as reservas ativas no período que se cruza com o período desejado
        reserved_room_ids = db.query(Reservations.room_id).filter(
            Reservations.status.in_(["booked", "checked_in"]),
            Reservations.check_in < check_out,
            Reservations.check_out > check_in
        ).subquery()

        # pega os quartos que não estão reservados no periodo, ativos, não deletados e não estão em manutenção
        available_rooms = db.query(Rooms).filter(
            Rooms.hotel_id == hotel_id,
            Rooms.status != "maintenance",
            Rooms.is_active == True,
            Rooms.is_deleted == False,
            ~Rooms.id.in_(reserved_room_ids)
        ).all()

        return available_rooms