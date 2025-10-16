from math import ceil

def calc_price(reservation):
    if reservation.Reservations.status != 'canceled':
        if not reservation.Reservations.check_out or not reservation.Reservations.check_in:
            return 0
        days = reservation.Reservations.check_out - reservation.Reservations.check_in
        total_days = ceil(days.total_seconds() / (24 * 3600))
        price = reservation.Rooms.price * total_days
        return price
    else:
        return 0