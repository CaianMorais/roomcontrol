from utils.flash import add_flash_message

def guest_updater(request, guest, email, phone_number, db):
    guest.email = email
    guest.phone_number = phone_number

    db.commit()
    db.refresh(guest)

    add_flash_message(request, f"Cadastro de {guest.name} editado com sucesso!", "success")