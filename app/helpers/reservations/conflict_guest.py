from models.reservations import Reservations

def conflict_guest(guest_id, check_in, check_out, db):
    guest_conflict = db.query(Reservations).filter(
        Reservations.status.not_in(["canceled", "checked_out"]),
        Reservations.guest_id == guest_id,
        Reservations.check_in < check_out,
        Reservations.check_out > check_in
    ).first()

    return guest_conflict