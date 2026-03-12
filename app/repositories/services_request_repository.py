from sqlalchemy.orm import Session
from app.models.services import Services
from app.models.reservations import Reservations
from app.models.guest import Guest
from app.models.rooms import Rooms

class ServicesRequestRepository:

    @staticmethod
    def find_by_id(db: Session, hotel_id: int, request_id: int):
        return db.query(Services, Guest, Reservations, Rooms) \
        .join(Guest, Services.guest_id == Guest.id) \
        .join(Reservations, Services.reservation_id == Reservations.id) \
        .join(Rooms, Rooms.id == Services.room_id) \
        .filter(Services.id==request_id, Guest.hotel_id==hotel_id) \
        .first()