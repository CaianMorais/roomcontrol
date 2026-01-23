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

    db.commit()

    return hotel, room

def test_api_get_rooms_ok(client, db_session):
    hotel, room = seed(db_session)

    response = client.get(f"/api/rooms?hotel_id={hotel.id}")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1

    assert data[0]["id"] == room.id
    assert data[0]["room_number"] == room.room_number
    assert data[0]["status"] == room.status
    assert data[0]["hotel"]["id"] == hotel.id