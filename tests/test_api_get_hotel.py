from app.models.hotel import Hotel

def seed(db):
    hotel = Hotel(
        name="Hotel Teste",
        login="hotelteste",
        password="senhateste",
        address="Teste, 123",
        city="Teste",
        state="TS",
        zip_code="12345678",
        phone_number="11912345678",
        email="teste@teste.com",
        cnpj="12345678000190",
        is_active=True,
    )
    db.add(hotel); db.flush()

    db.commit()

    return hotel

def test_api_get_hotel_ok(client, db_session):
    hotel = seed(db_session)

    response = client.get(f"/api/hotels?cnpj={hotel.cnpj}&name={hotel.name}")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1

    assert data[0]["id"] == hotel.id
    assert data[0]["name"] == hotel.name
    assert data[0]["cnpj"] == hotel.cnpj