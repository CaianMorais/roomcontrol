from app.utils.flash import add_flash_message
from fastapi.responses import RedirectResponse
from app.core.config import SessionLocal
from app.models.guest import Guest
from fastapi import HTTPException

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_guest(request, guest_id, hotel_id, db):
    guest = db.query(Guest).filter(Guest.hotel_id == hotel_id).filter(Guest.id == guest_id).first()
    if not guest:
        add_flash_message(request, "Hóspede inexistente", "danger")
        raise HTTPException(status_code=303, headers={"Location": "/dashboard"})
    return guest