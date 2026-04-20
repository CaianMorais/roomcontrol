from sqlalchemy.orm import Session, joinedload
from app.models.hotel import Hotel
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
    
    @staticmethod
    def update(db: Session, service: Services, new_status: str):
        service.status = new_status
        db.commit()
        db.refresh(service)

class ApiServicesRequestRepository:

    @staticmethod
    def base_query(db: Session, hotel_id: int = None):
        query = (
            db.query(Services)
            .options(
                joinedload(Services.reservation).joinedload(Reservations.guest),
                joinedload(Services.reservation).joinedload(Reservations.room).joinedload(Rooms.hotel)
            )
        )

        if hotel_id:
            query = query.join(Services.room) \
            .join(Rooms.hotel) \
            .filter(Hotel.id == hotel_id)

        return query
    
    @staticmethod
    def filter_requests_by_hotel(query, hotel_id: int = None, hotel_name: str = None):
        if hotel_id:
            query = query.join(Services.room) \
            .join(Rooms.hotel) \
            .filter(Hotel.id == hotel_id)
        if hotel_name:
            query = query.join(Services.room) \
            .join(Rooms.hotel) \
            .filter(Hotel.name.ilike(f'%{hotel_name}%'))
        return query
    
    @staticmethod
    def filter_requests(query, reservation_id: int = None, guest_cpf: str = None, guest_name: str = None, room_number: str = None, status: str = None):
        if reservation_id:
            query = query.filter(Services.reservation_id == reservation_id)
        if guest_cpf:
            query = query.join(Services.guest).filter(Guest.cpf == guest_cpf)
        if guest_name:
            query = query.join(Services.guest).filter(Guest.name.ilike(f'%{guest_name}%'))
        if room_number:
            query = query.join(Services.room).filter(Rooms.room_number == room_number)
        if status:
            query = query.filter(Services.status.ilike(f'%{status}%'))

        return query