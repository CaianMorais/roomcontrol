from sqlalchemy import case
from models.reservations import Reservations

def order_reservations(query):
    reservations = query.order_by(
        case(
            (Reservations.status == "booked", 1),
            (Reservations.status == "checked_in", 2),
            (Reservations.status == "checked_out", 3),
            (Reservations.status == "canceled", 4),
        ),
        Reservations.check_in,
        Reservations.id
    )
    return reservations