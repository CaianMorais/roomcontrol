from sqlalchemy import or_
from app.models.reservations import Reservations
from app.models.guest import Guest
from app.models.rooms import Rooms
import datetime
from app.utils.flash import add_flash_message
from fastapi import HTTPException

def filter_reservations(request, has_filter, query, search, room, status, interval_in, check_in, interval_out, check_out):
    if has_filter:
        if search:
            query = query.filter(
                or_(
                    Reservations.id == search,
                    Guest.name.ilike(f"%{search}%")
                )
            )

        if room:
            query = query.filter(Rooms.id == room)
            
        if status:
            query = query.filter(Reservations.status == status)

        if interval_in and check_in:
            try:
                check_in_dt = datetime.datetime.strptime(check_in, '%Y-%m-%dT%H:%M')
                if interval_in == 'before':
                    query = query.filter(Reservations.check_in < check_in_dt)
                elif interval_in == 'after':
                    query = query.filter(Reservations.check_in > check_in_dt)
            except ValueError as e:
                add_flash_message(request, f"Erro: {e}", "danger")

        if interval_out and check_out:
            try:
                check_out_dt = datetime.datetime.strptime(check_out, "%Y-%m-%dT%H:%M")
                if interval_out == 'before':
                    query = query.filter(Reservations.check_out < check_out_dt)
                elif interval_out == 'after':
                    query = query.filter(Reservations.check_out > check_out_dt)
            except ValueError as e:
                add_flash_message(request, f"Erro: {e}", "danger")

        if len(query.all()) == 0:
            add_flash_message(request, 'Nenhuma reserva encontrada com os filtros aplicados.', "warning")
            raise HTTPException(status_code=303, headers={"Location": "/dashboard_reservations"})
        elif len(query.all()) > 0:
            add_flash_message(request, "Filtro aplicado", "success")
    
    return query