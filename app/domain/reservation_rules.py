from typing import Optional, Tuple

def decide_fast_update(
    reservation_status: str,
    room_status: str,
) -> Tuple[bool, Optional[str], Optional[str]]:

    if reservation_status == 'booked' and room_status == 'available':
        return True, 'checked_in', 'occupied'

    if reservation_status == 'checked_in' and room_status == 'occupied':
        return True, 'checked_out', 'available'

    return False, None, None
