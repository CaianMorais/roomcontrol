import datetime
from app.utils.flash import add_flash_message
from fastapi import HTTPException

def ckeckin_to_checkout(request, check_out, reservation, db):
    if check_out and reservation.Reservations.status == 'checked_in' and reservation.Rooms.status == 'occupied':
        reservation.Reservations.status = 'checked_out'
        reservation.Reservations.check_out = datetime.datetime.now()
        reservation.Rooms.status = 'available'
        db.commit()
        db.refresh(reservation.Reservations)
        db.refresh(reservation.Rooms)
        add_flash_message(request, "Reserva atualizada com sucesso!", 'success')
    elif check_out and (reservation.Reservations.status != 'checked_in' or reservation.Rooms.status != 'occupied'):
        raise HTTPException(status_code=303, headers={"Location": f'/dashboard_reservations/manage/{reservation.Reservations.id}'})