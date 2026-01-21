from app.models.reservations import Reservations
from app.models.guest import Guest

def guest_availability(hotel_id, check_in, check_out, db):
    reserved_guest_ids = db.query(Reservations.guest_id).filter(
        Reservations.check_in < check_out,
        Reservations.check_out > check_in,
        Reservations.status.in_(["booked", "checked_in"])
    ).subquery()

    available_guests = db.query(Guest).filter(
        Guest.hotel_id == hotel_id,
        ~Guest.id.in_(reserved_guest_ids)
    ).all()

    return available_guests