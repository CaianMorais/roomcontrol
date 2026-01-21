import datetime
from conftest import set_session_cookie

from app.models.hotel import Hotel
from app.models.rooms import Rooms
from app.models.guest import Guest
from app.models.reservations import Reservations
from app.models.services import Services


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
        name="João da Silva",
        cpf="12345678900",
        is_deleted=False)
    db.add(guest); db.flush()

    res = Reservations(
        guest_id=guest.id,
        room_id=room.id,
        check_in=datetime.datetime.now(),
        check_out=datetime.datetime.now() + datetime.timedelta(days=1),
        status="checked_in",
        allow_request_services=True,
    )
    db.add(res); db.flush()

    srv = Services(
        reservation_id=res.id,
        guest_id=guest.id,
        room_id=room.id,
        request="Pedido de serviço teste",
        status="pending",
    )
    db.add(srv)
    db.commit()

    return hotel, room, guest, res, srv


def test_table_services_requests_ok(client, db_session):
    hotel, room, guest, res, srv = seed(db_session)

    set_session_cookie(client, {"hotel_id": hotel.id})

    r = client.get(f"/api/table_services_requests?hotel_id={hotel.id}")
    assert r.status_code == 200

    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["id"] == srv.id
