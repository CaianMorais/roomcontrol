from app.domain.guest_rules import guest_can_be_deleted

def test_guest_can_be_deleted_reservation_checked_out():
    ok, is_deleted, reservation_status = guest_can_be_deleted(False, 'checked_out')

    assert ok is True
    assert is_deleted is True
    assert reservation_status is None

def test_guest_can_be_deleted_reservation_canceled():
    ok, is_deleted, reservation_status = guest_can_be_deleted(False, 'canceled')

    assert ok is True
    assert is_deleted is True
    assert reservation_status is None

def test_guest_cannot_be_deleted_booked_reservation():
    ok, is_deleted, reservation_status = guest_can_be_deleted(False, 'booked')

    assert ok is False
    assert is_deleted is False
    assert reservation_status == "Hóspede possui reserva ativa."

def test_guest_cannot_be_deleted_checked_in_reservation():
    ok, is_deleted, reservation_status = guest_can_be_deleted(False, 'checked_in')

    assert ok is False
    assert is_deleted is False
    assert reservation_status == "Hóspede possui reserva ativa."

def test_guest_cannot_be_deleted_already_deleted():
    ok, is_deleted, reservation_status = guest_can_be_deleted(True, 'checked_in')

    assert ok is False
    assert is_deleted is False
    assert reservation_status == "Hóspede já está deletado."