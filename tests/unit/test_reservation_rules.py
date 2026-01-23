from app.domain.reservation_rules import decide_fast_update

def test_fast_update_from_booked_to_checked_in():
    ok, reservation_status, room_status = decide_fast_update('booked', 'available')

    assert ok is True
    assert reservation_status == 'checked_in'
    assert room_status == 'occupied'

def test_fast_update_from_checked_in_to_checked_out():
    ok, reservation_status, room_status = decide_fast_update('checked_in', 'occupied')

    assert ok is True
    assert reservation_status == 'checked_out'
    assert room_status == 'available'

def test_fast_update_conflict():
    ok, reservation_status, room_status = decide_fast_update('booked', 'occupied')

    assert ok is False
    assert reservation_status is None
    assert room_status is None