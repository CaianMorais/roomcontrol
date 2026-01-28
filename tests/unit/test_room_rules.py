from app.domain.room_rules import room_can_be_inactivated

def test_room_can_be_inactivated_checked_out_reservations():
    ok, is_inactivated, message = room_can_be_inactivated(True, False, 'checked_out')

    assert ok is True
    assert is_inactivated is True
    assert message == "Quarto foi inativado."

def test_room_cannot_be_inactivated_canceled_reservation():
    ok, is_inactivated, message = room_can_be_inactivated(True, False, 'canceled')

    assert ok is True
    assert is_inactivated is True
    assert message == "Quarto foi inativado."

def test_room_cannot_be_inactivated_booked_reservation():
    ok, is_inactivated, message = room_can_be_inactivated(False, False, 'booked')

    assert ok is False
    assert is_inactivated is False
    assert message == "Quarto não pode ser inativado."

def test_room_cannot_be_inactivated_checked_in_reservation():
    ok, is_inactivated, message = room_can_be_inactivated(False, False, 'checked_in')

    assert ok is False
    assert is_inactivated is False
    assert message == "Quarto não pode ser inativado."