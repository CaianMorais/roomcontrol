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
            db.query(Reservations, Rooms.room_number, Guest.is_deleted, Guest.name, Guest.id)
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
