from app.models.reservations import Reservations
from app.models.rooms import Rooms

def room_availability(db, check_in, check_out, hotel_id):
    # Quartos disponíveis
    reserved_room_ids = db.query(Reservations.room_id).filter(
        Reservations.status.in_(["booked", "checked_in"]),
        Reservations.check_in < check_out,
        Reservations.check_out > check_in
    ).subquery()

    available_rooms = db.query(Rooms).filter(
        Rooms.hotel_id == hotel_id,
        Rooms.status != "maintenance",
        Rooms.is_active == True,
        ~Rooms.id.in_(reserved_room_ids)
    ).all()

    return available_rooms