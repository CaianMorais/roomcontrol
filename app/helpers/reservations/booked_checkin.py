import datetime
from app.utils.flash import add_flash_message
from fastapi import HTTPException

def booked_to_checkin(request, check_in, reservation, db):
    if check_in and reservation.Reservations.status == 'booked' and reservation.Rooms.status == 'available':
        reservation.Reservations.status = 'checked_in'
        check_in_now = datetime.datetime.now()
        reservation.Reservations.check_in = check_in_now
        if check_in_now > reservation.Reservations.check_out:
            reservation.Reservations.check_out = check_in_now + datetime.timedelta(days=1)
            add_flash_message(request, "Devido ao conflito de datas, a previsão do check-out foi alterada automaticamente.", "warning")
        reservation.Rooms.status = 'occupied'
        db.commit()
        db.refresh(reservation.Reservations)
        db.refresh(reservation.Rooms)
        add_flash_message(request, "Reserva atualizada com sucesso!", 'success')
    elif check_in and (reservation.Reservations.status != 'booked' or reservation.Rooms.status != 'available'):
        raise HTTPException(status_code=303, headers={"Location": f'/dashboard_reservations/manage/{reservation.Reservations.id}'})
    
