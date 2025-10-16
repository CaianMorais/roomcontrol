import datetime

def fast_update_reservation(reservation, room, db):
    if reservation.status == 'booked' and room.status == 'available':
        reservation.status = 'checked_in'
        check_in_now = datetime.datetime.now()
        reservation.check_in = check_in_now
        if check_in_now > reservation.check_out:
            reservation.check_out = check_in_now + datetime.timedelta(days=1)
        room.status = 'occupied'
    elif reservation.status == 'checked_in' and room.status == 'occupied':
        reservation.status = 'checked_out'
        reservation.check_out = datetime.datetime.now()
        room.status = 'available'
    else:
        return {
            "message": f"Não foi possível modificar essa reserva."
        }
    
    db.commit()
    db.refresh(reservation)
    db.refresh(room)