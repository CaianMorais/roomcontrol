from app.domain.reservation_rules import decide_fast_update
from app.repositories.reservation_repository import ApiReservationRepository, ReservationRepository
from app.models.reservations import Reservations
import datetime
from app.repositories.room_repository import RoomsRepository

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
    
    @staticmethod
    def create_reservation(db, check_in, check_out, check_in_now, room, guest):
        # validações redundantes, o front-end já faz, mas é bom garantir
        if check_out <= check_in:
            return None, "Data de check-out deve ser posterior à data de check-in."
        if check_out < datetime.datetime.now():
            return None, "O horário de check-out não pode ser menor que o horário atual."
        
        if not check_in_now:
            status = 'booked'
        elif check_in_now:
            status = 'checked_in'
            room.status = 'occupied'
        else:
            return None, "Data de check-in inválida."
        
        new_reservation = Reservations(
            guest_id=guest.id,
            room_id=room.id,
            check_in=check_in,
            check_out=check_out,
            status=status
        )

        return ReservationRepository.create(db, new_reservation), None
        
    @staticmethod
    def get_reservation(db, reservation_id, hotel_id):
        reservation = ReservationRepository.find_by_id(db, reservation_id, hotel_id)
        if reservation:
            return reservation, None
        else:
            return None, "Reserva não encontrada"
        
    @staticmethod
    def get_reservation_price(reservation):
        return ReservationRepository.calculate_price(reservation)
        
    @staticmethod
    def update_status_from_manage(db, check_in, check_out, cancel, reservation):
        # se check-in for true, verifica se o hóspede já tem uma reserva checked_in
        if check_in:
            guest_is_occupied = ReservationRepository.check_guest_is_available(db, reservation)
            if guest_is_occupied:
                return reservation.Reservations, "O hóspede tem uma reserva ativa neste momento."
        # se check-in for true, tenta realizar o check-in
        if check_in and reservation.Reservations.status == 'booked' and reservation.Rooms.status == 'available':
            reservation.Reservations.status = 'checked_in'
            check_in_now = datetime.datetime.now()
            reservation.Reservations.check_in = check_in_now

            if check_in_now > reservation.Reservations.check_out:
                reservation.Reservations.check_out = check_in_now + datetime.timedelta(days=1)
            reservation.Rooms.status = 'occupied'
        elif check_in and (reservation.Reservations.status != 'booked' or reservation.Rooms.status != 'available'):
            return reservation.Reservations, "Erro ao realizar check-in."
        
        # se check-out for true, tenta realizar o check-out
        if check_out and reservation.Reservations.status == 'checked_in' and reservation.Rooms.status == 'occupied':
            reservation.Reservations.status = 'checked_out'
            reservation.Reservations.check_out = datetime.datetime.now()
            reservation.Rooms.status = 'available'
        elif check_out and (reservation.Reservations.status != 'checked_in' or reservation.Rooms.status != 'occupied'):
            return reservation.Reservations, "Erro ao realizar check-out."
        
        # se cancel for true, tenta realizar o cancelamento
        if cancel and reservation.Reservations.status == 'canceled':
            return reservation, "A reserva já está cancelada."
        elif cancel and reservation.Reservations.status == 'checked_out':
            return reservation.Reservations, "A reserva já foi encerrada."
        elif cancel and (reservation.Reservations.status == 'booked' or reservation.Reservations.status == 'checked_in'):
            reservation.Reservations.status = 'canceled'
            reservation.Reservations.check_out = datetime.datetime.now()
            reservation.Rooms.status = 'available'
        
        return ReservationRepository.update(db, reservation), None
    
    @staticmethod
    def update_status_from_table(db, reservation, room):

        # valida se a reserva e o quarto estão em estados que permitem atualização
        ok, new_reservation_status, new_room_status = decide_fast_update(
            reservation.Reservations.status,
            room.status,
        )

        if not ok:
            return None, "Não foi possível modificar esta reserva!"
        
        now = datetime.datetime.now()

        if new_reservation_status == 'checked_in':
            reservation.Reservations.status = new_reservation_status
            reservation.Reservations.check_in = now

            if now > reservation.Reservations.check_out:
                reservation.Reservations.check_out = now + datetime.timedelta(days=1)

        elif new_reservation_status == 'checked_out':
            reservation.Reservations.status = new_reservation_status
            reservation.Reservations.check_out = now
            
        room.status = new_room_status

        reservation_updated = ReservationRepository.update(db, reservation)
        room_updated = RoomsRepository.update(db, room)

        if not reservation_updated or not room_updated:
            return None, "Erro ao atualizar a reserva"
        
        return reservation_updated, None
    
    @staticmethod
    def change_requests_services(db, reservation):
        # se a reserva estiver habilitada a solicitar serviços
        if reservation.Reservations.allow_request_services:
            reservation.Reservations.allow_request_services = False
            message = "O hóspede não está mais autorizado a solicitar serviços para essa reserva"

        else:
            reservation.Reservations.allow_request_services = True
            message = "O hóspede está autorizado a solicitar serviços para essa reserva"

        reservation_updated = ReservationRepository.update(db, reservation)
        if not reservation_updated:
            return None, "Erro ao realizar operação", None
        
        return reservation_updated, None, message

class ApiReservationService:

    @staticmethod
    def get_reservations(db, hotel_id):
        return ApiReservationRepository.base_query(db, hotel_id)
    
    @staticmethod
    def filter_reservations(query, hotel_id: int = None, hotel_name: str = None, guest_id: int = None, guest_name: str = None, room_number: str = None, check_in: str = None, check_out: str = None):

        if hotel_id or hotel_name:
            query = ApiReservationRepository.apply_hotel_filters(
                query=query,
                hotel_id=hotel_id,
                hotel_name=hotel_name
            )
            
        if guest_id or guest_name or room_number or check_in or check_out:
            query = ApiReservationRepository.apply_filters(
                query=query,
                guest_id=guest_id,
                guest_name=guest_name,
                room_number=room_number,
                check_in=check_in,
                check_out=check_out
            )

        return query