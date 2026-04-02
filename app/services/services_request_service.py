from app.repositories.services_request_repository import ServicesRequestRepository
from app.models.services import Services
from fastapi.responses import JSONResponse

class ServicesRequestService:

    @staticmethod
    def get_request(db, hotel_id, request_id):
        request = ServicesRequestRepository.find_by_id(db, hotel_id, request_id)
        if not request:
            return None, "Pedido não encontrado."
        return request, None
    
    @staticmethod
    def update_request_status(request, db, new_status, service_id):
        if new_status not in ("pending", "in_progress", "completed"):
            return {
                "ok": False,
                "message": "Status inválido fornecido.",
                "new_status": None
            }

        if not service_id:
            return {
                "ok": False,
                "message": "ID do pedido de serviço não encontrado na sessão.",
                "new_status": None
            }
        
        service = ServicesRequestRepository.find_by_id(db, request.session.get('hotel_id'), service_id)

        if not service:
            return {
                "ok": False,
                "message": "Pedido de serviço não encontrado.",
                "new_status": None
            }
            
        
        if service.Services.status == "completed":
            return {
                "ok": False,
                "message": "O pedido já foi concluído e não pode ser alterado.",
                "new_status": service.Services.status
            }

        if service.Services.status == new_status:
            return {
                "ok": False,
                "message": "O pedido já está com esse status.",
                "new_status": new_status
            }

        ServicesRequestRepository.update(db, service.Services, new_status)
        
        return {
            "ok": True,
            "message": "Status do pedido atualizado com sucesso.",
            "new_status": new_status
        }