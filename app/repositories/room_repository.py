from sqlalchemy.orm import Session
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
