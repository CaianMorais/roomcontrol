from models.guest import Guest
from models.rooms import Rooms
from models.reservations import Reservations
from models.services import Services
from sqlalchemy import desc
from utils.flash import add_flash_message
from fastapi import HTTPException

def create_request_service(request, db, reservation_id, service_description):
    reserva = db.query(Reservations).filter(Reservations.id == reservation_id).first()
    if not reserva or reserva.status != 'checked_in':
        add_flash_message(request, 'Reserva encerrada ou inexistente. Verifique os dados e tente novamente.', 'danger')
        raise HTTPException(status_code=303, headers={"Location": "/guests"})
    
    if reserva.allow_request_services == False:
        add_flash_message(request, 'Pedidos de serviços estão bloqueados na sua reserva!', 'danger')
        raise HTTPException(status_code=303, headers={"Location": "/guests"})
    
    new_request = Services(
        reservation_id=reserva.id,
        guest_id=reserva.guest_id,
        room_id=reserva.room_id,
        request=service_description,
        status='pending',
    )

    db.add(new_request)
    db.commit()
    db.refresh(new_request)

    return True