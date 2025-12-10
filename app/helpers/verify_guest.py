from utils.flash import add_flash_message
from core.config import SessionLocal
from models.guest import Guest
from fastapi import HTTPException

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_guest_by_id(request, guest_id, hotel_id, db):
    guest = db.query(Guest) \
        .filter(Guest.id == guest_id) \
        .filter(Guest.hotel_id == hotel_id) \
        .filter(Guest.is_deleted == False) \
        .first()
    if not guest:
        add_flash_message(request, "Hóspede inexistente", "danger")
        raise HTTPException(status_code=303, headers={"Location": "/dashboard"})
    return guest

def verify_guest_by_cpf(request, cpf, hotel_id, db):
    guest = db.query(Guest) \
    .filter(Guest.cpf == cpf) \
    .filter(Guest.hotel_id == hotel_id) \
    .filter(Guest.is_deleted == False) \
    .first()
    if not guest:
        add_flash_message(request, "Hóspede inexistente", "danger")
        raise HTTPException(status_code=303, headers={"Location": "/dashboard"})
    return guest