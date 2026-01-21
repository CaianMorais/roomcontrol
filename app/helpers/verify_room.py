from app.utils.flash import add_flash_message
from app.core.config import SessionLocal
from app.models.rooms import Rooms
from fastapi import HTTPException

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_room(request, room_id, hotel_id, db):
    room = db.query(Rooms).filter(Rooms.id == room_id).filter(Rooms.hotel_id == hotel_id).first()
    if not room:
        add_flash_message(request, "Quarto inexistente", "danger")
        raise HTTPException(status_code=303, headers={"Location": "/dashboard"})
    return room