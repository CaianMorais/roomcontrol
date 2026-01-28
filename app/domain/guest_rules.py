from typing import Optional, Tuple

def guest_can_be_deleted(
    guest_is_deleted: bool,
    reservation_status: str
) -> Tuple[bool, Optional[bool], Optional[str]]:
    #retorna ok, is_deleted, mensagem de status

    if guest_is_deleted:
        return False, False, "Hóspede já está deletado."
    
    if reservation_status in ['booked', 'checked_in']:
        return False, False, "Hóspede possui reserva ativa."

    return True, True, None