from app.models.reservations import Reservations
from app.utils.flash import add_flash_message
from starlette.responses import RedirectResponse

def guest_delete(request, db, guest):
    ## verifica se o hospede tem uma reserva ativa ou agendada antes de deletar
    reservations = db.query(Reservations).filter_by(guest_id=guest.id).all()
    for res in reservations:
        if res.status == 'booked' or res.status == 'checked_in':
            add_flash_message(request, "Esse hóspede tem uma reserva ativa ou agendada no momento, impossível deletar.", 'warning')
            return RedirectResponse(url="/dashboard_guests", status_code=303)
    
    guest.is_deleted = True
    db.commit()
    add_flash_message(request, f"O hóspede {guest.name} foi removido.")