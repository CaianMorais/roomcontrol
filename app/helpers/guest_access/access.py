from models.guest import Guest
from models.rooms import Rooms
from models.reservations import Reservations
from models.services import Services
from sqlalchemy import desc
from utils.flash import add_flash_message
from fastapi import HTTPException

def find_guest(request, db, cpf):
    guest = db.query(Guest) \
        .filter(Guest.cpf == cpf) \
        .first()

    if not guest:
        add_flash_message(request, 'CPF não encontrado. Verifique e tente novamente.', 'danger')
        raise HTTPException(status_code=303, headers={"Location": "/guests"})
    
    return guest

def find_reservation(request, db, res, guest):
    reservation = db.query(Reservations, Rooms) \
        .join(Rooms, Reservations.room_id == Rooms.id) \
        .filter(Reservations.id == res) \
        .order_by(desc(Reservations.created_at)) \
        .first()

    if not reservation or reservation.Reservations.guest_id != guest.id or reservation.Reservations.status != 'checked_in':
        add_flash_message(request, 'Reserva encerrada ou inexistente. Verifique os dados e tente novamente.', 'danger')
        raise HTTPException(status_code=303, headers={"Location": "/guests"})
    
    return reservation
    
def find_services(db, reservation):
    services = db.query(Services) \
        .filter(Services.reservation_id == reservation.Reservations.id) \
        .order_by(desc(Services.created_at)) \
        .all()
    
    return services
