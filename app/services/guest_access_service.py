from sqlalchemy.orm import Session

from app.repositories.guest_access_repository import GuestAccessRepository


class GuestAccessService:

    @staticmethod
    def get_guest_by_cpf(db: Session, cpf: str):
        guest = GuestAccessRepository.find_guest_by_cpf(db, cpf)
        if not guest:
            return None, "CPF não encontrado. Verifique e tente novamente."
        return guest, None

    @staticmethod
    def get_active_reservation(db: Session, reservation_id: int, guest_id: int):
        reservation = GuestAccessRepository.find_active_reservation(db, reservation_id, guest_id)
        if not reservation:
            return None, "Reserva encerrada ou inexistente. Verifique os dados e tente novamente."
        return reservation, None

    @staticmethod
    def get_services(db: Session, reservation_id: int):
        return GuestAccessRepository.find_services_by_reservation(db, reservation_id)

    @staticmethod
    def create_service_request(db: Session, reservation_id: int, description: str):
        reservation = GuestAccessRepository.find_reservation_by_id(db, reservation_id)

        if not reservation or reservation.status != 'checked_in':
            return None, "Reserva encerrada ou inexistente. Verifique os dados e tente novamente."

        if not reservation.allow_request_services:
            return None, "Pedidos de serviços estão bloqueados na sua reserva."

        service = GuestAccessRepository.create_service_request(
            db,
            reservation_id=reservation.id,
            guest_id=reservation.guest_id,
            room_id=reservation.room_id,
            description=description
        )
        return service, None

    @staticmethod
    def get_service_by_id(db: Session, service_id: int):
        service = GuestAccessRepository.find_service_by_id(db, service_id)
        if not service:
            return None, "Solicitação de serviço não encontrada."
        return service, None