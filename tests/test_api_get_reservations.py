import datetime

from app.models.hotel import Hotel
from app.models.rooms import Rooms
from app.models.guest import Guest
from app.models.reservations import Reservations

def seed(db):
    hotel = Hotel(
        name="Hotel Teste",
        login="hotelteste",
        password="senhateste",
        cnpj="12.345.678/0001-90",
        is_active=True,
    )
    db.add(hotel); db.flush()

    room = Rooms(
        hotel_id=hotel.id,
        room_number="101",
        type="1", 
        status="available",
        is_active=True
    )
    db.add(room); db.flush()

    guest = Guest(
        hotel_id=hotel.id,
        name="Teste da Silva",
        cpf="12345678900",
        is_deleted=False)
    db.add(guest); db.flush()

    reservation = Reservations(
        guest_id=guest.id,
        room_id=room.id,
        check_in=datetime.datetime.now(),
        check_out=datetime.datetime.now() + datetime.timedelta(days=1),
        status="checked_in",
        allow_request_services=True,
    )
    db.add(reservation); db.flush()

    db.commit()

    return hotel, room, guest, reservation

def test_api_get_reservations_ok(client, db_session):
    hotel, room, guest, reservation = seed(db_session)

    response = client.get(f"/api/reservations?hotel_name={hotel.name}")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1

    assert data[0]["id"] == reservation.id
    assert data[0]["guest"]["id"] == guest.id
    assert data[0]["room"]["id"] == room.id
    assert data[0]["room"]["hotel"]["id"] == hotel.id