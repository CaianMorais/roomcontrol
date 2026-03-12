from app.repositories.services_request_repository import ServicesRequestRepository
from app.models.services import Services

class ServicesRequestService:

    @staticmethod
    def get_request(db, hotel_id, request_id):
        request = ServicesRequestRepository.find_by_id(db, hotel_id, request_id)
        if not request:
            return None, "Pedido não encontrado."
        return request, None