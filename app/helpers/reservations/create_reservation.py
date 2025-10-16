import datetime
from fastapi import HTTPException
from app.utils.flash import add_flash_message
from app.models.reservations import Reservations

def verify_and_create_reservation(request, check_in, check_out, room, guest, db):
    if check_out <= check_in:
        add_flash_message(request, "Data de check-out deve ser posterior à data de check-in.", "danger")
        raise HTTPException(status_code=303, headers={"Location": "/dashboard_reservations/new"})
    
    if check_out < datetime.datetime.now():
        add_flash_message(request, "O horário de check-out não pode ser menor que o horário atual.", "danger")
        raise HTTPException(status_code=303, headers={"Location": "/dashboard_reservations/new"})

    
    if check_in > datetime.datetime.now():
        status= 'booked'
    elif check_in <= datetime.datetime.now():
        status= 'checked_in'
        room.status = 'occupied'
    else:
        add_flash_message(request, "Data de check-in inválida.", "danger")
        raise HTTPException(status_code=303, headers={"Location": "/dashboard_reservations/new"})

    new_reservation = Reservations(
        guest_id=guest.id,
        room_id=room.id,
        check_in=check_in,
        check_out=check_out,
        status=status
    )

    db.add(new_reservation)
    db.commit()