from app.models.services import Services
from app.models.reservations import Reservations
from app.models.guest import Guest
from app.models.rooms import Rooms
from app.utils.flash import add_flash_message
from fastapi import HTTPException

def query_requests(request, db, hotel_id, request_id):

    service_request = db.query(Services, Guest, Reservations, Rooms) \
        .join(Guest, Services.guest_id == Guest.id) \
        .join(Reservations, Services.reservation_id == Reservations.id) \
        .join(Rooms, Rooms.id == Services.room_id) \
        .filter(Services.id==request_id, Guest.hotel_id==hotel_id) \
        .first()
    
    if not service_request:
        add_flash_message(request, "Houve um erro ao tentar abrir o pedido.", "warning")
        raise HTTPException(status_code=303, headers={"Location": "/dashboard_services"})
    
    return service_request
    