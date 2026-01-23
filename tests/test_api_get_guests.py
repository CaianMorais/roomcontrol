import datetime

from app.models.hotel import Hotel
from app.models.guest import Guest

def seed(db):
    hotel = Hotel(
        name="Hotel Teste",
        login="hotelteste",
        password="senhateste",
        cnpj="12.345.678/0001-90",
        is_active=True,
    )
    db.add(hotel); db.flush()

    guest = Guest(
        hotel_id=hotel.id,
        name="Teste da Silva",
        cpf="12345678900",
        is_deleted=False)
    db.add(guest); db.flush()

    db.commit()

    return hotel, guest

def test_api_get_guests_ok(client, db_session):
    hotel, guest = seed(db_session)

    response = client.get(f"/api/guests?hotel_id={hotel.id}")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1

    assert data[0]["id"] == guest.id
    assert data[0]["name"] == guest.name
    assert data[0]["cpf"] == guest.cpf
    assert data[0]["hotel"]["id"] == hotel.id