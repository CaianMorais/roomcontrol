from app.repositories.reservation_repository import ReservationRepository
import datetime

class ReservationService:

    @staticmethod
    def list_reservations(db, hotel_id):
        return ReservationRepository.get_reservations(db, hotel_id)
    
    @staticmethod
    def filter_reservations(query, search, room, status, interval_in, check_in, interval_out, check_out):
        check_in_dt = None
        check_out_dt = None
        try:
            if interval_in and check_in:
                check_in_dt = datetime.datetime.strptime(check_in, '%Y-%m-%dT%H:%M')

            if interval_out and check_out:
                check_out_dt = datetime.datetime.strptime(check_out, '%Y-%m-%dT%H:%M')

        except ValueError:
            return None, "Formato de data inválido."
        
        query = ReservationRepository.apply_filters(
            query=query,
            search=search,
            room=room,
            status=status,
            interval_in=interval_in,
            check_in_dt=check_in_dt,
            interval_out=interval_out,
            check_out_dt=check_out_dt
        )

        return query, None

    @staticmethod
    def guest_has_conflict(db, guest_id, check_in, check_out):
        return ReservationRepository.check_guest_conflict(db, guest_id, check_in, check_out)
    
    @staticmethod
    def get_available_guests(db, hotel_id, check_in, check_out):
        return ReservationRepository.check_available_guests(db, hotel_id, check_in, check_out)
    
    @staticmethod
    def get_available_rooms(db, check_in, check_out, hotel_id):
        return ReservationRepository.check_available_rooms(db, hotel_id, check_in, check_out)