from typing import Optional, Tuple

def room_can_be_inactivated(
    room_is_active: bool,
    room_new_status: bool,
    reservation_status: str
) -> Tuple[bool, Optional[bool], Optional[str]]:
    
    if not room_is_active and not room_new_status :
        if reservation_status in ['booked', 'checked_in']:
            return False, False, "Quarto não pode ser inativado."
        
    return True, True, "Quarto foi inativado."
    
