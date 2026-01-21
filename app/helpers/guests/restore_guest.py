from app.models.guest import Guest
from app.utils.flash import add_flash_message

def restore_guest(request, db, name, email, cpf, phone_number, hotel_id):
    guest = db.query(Guest).filter(Guest.cpf == cpf).filter(Guest.hotel_id == hotel_id, Guest.is_deleted == True).first()
    guest.name = name
    guest.email = email if email else None
    guest.phone_number = phone_number if phone_number else None
    guest.is_deleted = False

    db.commit()
    db.refresh(guest)
    add_flash_message(request, "Hóspede cadastrado com sucesso, continue com a reserva", "success")