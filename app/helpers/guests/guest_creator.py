from models.guest import Guest
from utils.flash import add_flash_message

def guest_creator(request, name, cpf, email, phone_number, hotel_id, db):
    new_guest = Guest(
        name=name,
        cpf=cpf,
        email=email if email else None,
        phone_number=phone_number if phone_number else None,
        hotel_id=hotel_id
    )
    db.add(new_guest)
    db.commit()
    db.refresh(new_guest)
    add_flash_message(request, "Hóspede cadastrado com sucesso, continue com a reserva", "success")
    return new_guest