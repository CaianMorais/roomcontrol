from sqlalchemy.orm import Session
from app.repositories.main_repository import MainRepository


class MainService:

    @staticmethod
    def get_rooms_summary(db: Session, hotel_id: int) -> dict:
        return MainRepository.get_rooms_summary(db, hotel_id)

    @staticmethod
    def get_reservations_summary(db: Session, hotel_id: int) -> dict:
        return MainRepository.get_reservations_summary(db, hotel_id)

    @staticmethod
    def get_upcoming_checkins(db: Session, hotel_id: int):
        check_ins = MainRepository.get_upcoming_checkins(db, hotel_id)
        return [
            {
                "reservation_id": r.id,
                "check_in": r.check_in.strftime("%d/%m %H:%M"),
                "guest_name": g.name,
                "room_number": ro.room_number,
                "room_type": ro.type,
            }
            for r, g, ro in check_ins
        ]

    @staticmethod
    def get_services_summary(db: Session, hotel_id: int) -> dict:
        return MainRepository.get_services_summary(db, hotel_id)

    @staticmethod
    def get_recent_service_requests(db: Session, hotel_id: int):
        services = MainRepository.get_recent_service_requests(db, hotel_id)
        return [
            {
                "service_id": s.id,
                "request": s.request,
                "status": s.status,
                "room_number": ro.room_number,
                "guest_name": g.name,
                "created_at": s.created_at.strftime("%d/%m %H:%M"),
            }
            for s, g, ro in services
        ]

    @staticmethod
    def get_recent_activity(db: Session, hotel_id: int):
        logs = MainRepository.get_recent_activity(db, hotel_id)
        action_labels = {
            "create": "Criou",
            "update": "Atualizou",
            "delete": "Removeu",
        }
        entity_labels = {
            "guest": "hóspede",
            "room": "quarto",
            "reservation": "reserva",
            "service": "pedido de serviço",
        }
        items = []
        for log, collaborator in logs:
            actor = collaborator.firstname + " " + collaborator.lastname if collaborator else "Administrador"
            action = action_labels.get(log.action, log.action)
            entity = entity_labels.get(log.entity, log.entity)
            items.append({
                "actor": actor,
                "action": action,
                "entity": entity,
                "entity_id": log.entity_id,
                "created_at": log.created_at.strftime("%d/%m %H:%M"),
            })
        return items