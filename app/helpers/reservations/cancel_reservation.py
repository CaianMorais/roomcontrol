import datetime
from app.utils.flash import add_flash_message
from fastapi import HTTPException


def cancel_reservation(request, cancel, reservation, db):
    if cancel and reservation.Reservations.status == 'canceled':
        add_flash_message(request, "A reserva já está cancelada", 'warning')
        raise HTTPException(status_code=303, headers={"Location": f'/dashboard_reservations/manage/{reservation.Reservations.id}'})
    elif cancel and reservation.Reservations.status == 'checked_out':
        add_flash_message(request, "A reserva já foi encerrada", 'warning')
        raise HTTPException(status_code=303, headers={"Location": f'/dashboard_reservations/manage/{reservation.Reservations.id}'})
    elif cancel and (reservation.Reservations.status == 'booked' or reservation.Reservations.status == 'checked_in'):
        reservation.Reservations.status = 'canceled'
        reservation.Reservations.check_out = datetime.datetime.now()
        reservation.Rooms.status = 'available'
        db.commit()
        db.refresh(reservation.Reservations)
        db.refresh(reservation.Rooms)
        add_flash_message(request, "A reserva foi cancelada com sucesso", 'success')