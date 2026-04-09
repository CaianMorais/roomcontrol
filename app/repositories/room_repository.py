from sqlalchemy.orm import Session
from app.models.reservations import Reservations
from app.models.rooms import Rooms

class RoomsRepository:

    @staticmethod
    def base_query(db: Session, hotel_id: int):
        return (
            db.query(Rooms)
            .filter(
                Rooms.hotel_id == hotel_id,
                Rooms.is_deleted == False
            )
        )
    
    @staticmethod
    def get_rooms(db: Session, hotel_id: int):
        return RoomsRepository.base_query(db, hotel_id)
    
    @staticmethod
    def filter_rooms_by_types(query, room_types: list):
        if room_types:
            query = query.filter(Rooms.type.in_(room_types))
            return query
    
    @staticmethod
    def filter_rooms_by_status(query, statuses: list):
        if statuses:
            query = query.filter(Rooms.status.in_(statuses))
            return query

    @staticmethod
    def find_by_room_number(db: Session, hotel_id: int, room_number: int):
        return (
            db.query(Rooms)
            .filter(
                Rooms.hotel_id == hotel_id,
                Rooms.room_number == room_number
            )
            .first()
        )
    
    @staticmethod
    def find_by_id(db: Session, room_id: int, hotel_id: int):
        return (
            db.query(Rooms)
            .filter(
                Rooms.hotel_id == hotel_id,
                Rooms.id == room_id,
                Rooms.is_deleted == False
            )
            .first()
        )
    
    @staticmethod
    def create(db: Session, room: Rooms):
        db.add(room)
        db.commit()
        db.refresh(room)
        return room
    
    @staticmethod
    def check_active_reservations(db: Session, room: Rooms):
        return (
            db.query(Reservations) \
            .filter_by(room_id=room.id) \
            .all()
        )
    
    @staticmethod
    def update(db: Session, room: Rooms):
        db.commit()
        db.refresh(room)
        return room
    
    @staticmethod
    def soft_delete(db: Session, room: Rooms):
        room.is_deleted = True
        db.commit()
        db.refresh(room)
        return room