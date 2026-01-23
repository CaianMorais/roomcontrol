import datetime
from typing import Tuple
from app.domain.reservation_rules import decide_fast_update

def fast_update_reservation(reservation, room, db) -> Tuple[bool, str]:
    # usa regras definidas para decidir se é possível atualizar reserva e quarto
    ok, new_reservation_status, new_room_status = decide_fast_update(
        reservation.status,
        room.status,
    )
    if not ok:
        return False, "Não foi possível modificar esta reserva!"

    now = datetime.datetime.now()
    if new_reservation_status == 'checked_in':
        reservation.status = 'checked_in'
        reservation.check_in = now
        if now > reservation.check_out:
            reservation.check_out = now + datetime.timedelta(days=1)

    elif new_reservation_status == 'checked_out':
        reservation.status = 'checked_out'
        reservation.check_out = now
        
    room.status = new_room_status
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        return False, f"Erro ao atualizar a reserva: {str(e)}"
    
    db.refresh(reservation)
    db.refresh(room)
    return True, "Reserva atualizada com sucesso."