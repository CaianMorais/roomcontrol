from app.models.reservations import Reservations
from app.models.guest import Guest

def subquery_reservations(db):
    subquery = db.query(
        Reservations.guest_id,
        Reservations.check_in.label('reservation_check_in'),
        Reservations.status.label('reservation_status'),
        Reservations.id.label('reservation_id')
    ).filter(
        Reservations.status.in_(['booked', 'checked_in']),
        Reservations.guest_id == Guest.id
    ).order_by(
        Reservations.check_in
    ).subquery()

    return subquery