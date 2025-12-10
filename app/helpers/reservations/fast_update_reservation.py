import datetime
from typing import Tuple

def fast_update_reservation(reservation, room, db) -> Tuple[bool, str]:
    # Atualiza a reserva de forma rápida pela tabela de reservas
    # Retorna uma tupla com sucesso e mensagem
    updated = False
    if reservation.status == 'booked' and room.status == 'available':
        reservation.status = 'checked_in'
        check_in_now = datetime.datetime.now()
        reservation.check_in = check_in_now
        if check_in_now > reservation.check_out:
            reservation.check_out = check_in_now + datetime.timedelta(days=1)
        room.status = 'occupied'
        updated = True
    elif reservation.status == 'checked_in' and room.status == 'occupied':
        reservation.status = 'checked_out'
        reservation.check_out = datetime.datetime.now()
        room.status = 'available'
        updated = True

    if not updated:
        return False, "Não foi possível modificar esta reserva, há algum conflito entre o status do quarto e o status da reserva."
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        return False, f"Erro ao atualizar a reserva: {str(e)}"
    
    db.refresh(reservation)
    db.refresh(room)
    return True, "Reserva atualizada com sucesso."