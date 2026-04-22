import datetime
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.collaborator import Collaborator
from app.models.guest import Guest
from app.models.reservations import Reservations
from app.models.rooms import Rooms
from app.models.services import Services


class MainRepository:

    # ─── QUARTOS ─────────────────────────────────────────────────────────────
    # função que faz a contagem do quarto por status atual
    @staticmethod
    def get_rooms_summary(db: Session, hotel_id: int) -> dict:
        #consulta os quartos agrupando por status e contando quantos tem de cada
        rooms_by_status = (
            db.query(
                Rooms.status,
                func.count(Rooms.id).label("total")
            )
            .filter(
                Rooms.hotel_id == hotel_id,
                Rooms.is_deleted == False,
                Rooms.is_active == True,
            )
            .group_by(Rooms.status)
            .all()
        )
        
        # inicia um dicionário com os status existentes
        summary = {"occupied": 0, "available": 0, "maintenance": 0, "total": 0}

        # alimenta o dicionario com os valores retornados pela query e retorna
        for status, total in rooms_by_status:
            summary[status] = total
            summary["total"] += total

        return summary

    # ─── RESERVAS ────────────────────────────────────────────────────────────
    # função que conta as reservas relevantes (do dia) e agrupa por status 
    @staticmethod
    def get_reservations_summary(db: Session, hotel_id: int) -> dict:
        today = datetime.date.today()
        today_start = datetime.datetime.combine(today, datetime.time.min)
        today_end = datetime.datetime.combine(today, datetime.time.max)

        reservations_by_status = (
            db.query(
                Reservations.status,
                func.count(Reservations.id).label("total")
            )
            .join(Rooms, Rooms.id == Reservations.room_id)
            .filter(Rooms.hotel_id == hotel_id)
            .filter(Reservations.status.in_(["booked", "checked_in"]))
            .group_by(Reservations.status)
            .all()
        )

        # cria o dicionario com a contagem e o status das reservas
        summary = {"booked": 0, "checked_in": 0}
        
        # alimenta o dicioanrio com os valores retornados pela query e retorna
        for status, total in reservations_by_status:
            summary[status] = total

        # check-ins previstos para hoje (booked com check_in até fim do dia)
        summary["checkins_today"] = (
            db.query(func.count(Reservations.id))
            .join(Rooms, Rooms.id == Reservations.room_id)
            .filter(
                Rooms.hotel_id == hotel_id,
                Reservations.status == "booked",
                Reservations.check_in >= today_start,
                Reservations.check_in <= today_end,
            )
            .scalar()
        )

        # check-outs previstos para hoje (checked_in com check_out até fim do dia)
        summary["checkouts_today"] = (
            db.query(func.count(Reservations.id))
            .join(Rooms, Rooms.id == Reservations.room_id)
            .filter(
                Rooms.hotel_id == hotel_id,
                Reservations.status == "checked_in",
                Reservations.check_out >= today_start,
                Reservations.check_out <= today_end,
            )
            .scalar()
        )

        return summary

    # função para retornar as próximas reservas com check-in previsto para as próximas 24 horas
    @staticmethod
    def get_upcoming_checkins(db: Session, hotel_id: int, hours: int = 24):
        now = datetime.datetime.now()
        now_plus_24_hours = now + datetime.timedelta(hours=hours)

        return (
            db.query(Reservations, Guest, Rooms)
            .join(Rooms, Rooms.id == Reservations.room_id)
            .join(Guest, Guest.id == Reservations.guest_id)
            .filter(
                Rooms.hotel_id == hotel_id,
                Reservations.status == "booked",
                Reservations.check_in >= now,
                Reservations.check_in <= now_plus_24_hours,
            )
            .order_by(Reservations.check_in.asc())
            .limit(5)
            .all()
        )

    # ─── PEDIDOS DE SERVIÇO ───────────────────────────────────────────────────

    #função que retorna a quantidade de pedidos de serviço agrupados por status
    @staticmethod
    def get_services_summary(db: Session, hotel_id: int) -> dict:
        requests_by_status = (
            db.query(
                Services.status,
                func.count(Services.id).label("total")
            )
            .join(Rooms, Rooms.id == Services.room_id)
            .filter(
                Rooms.hotel_id == hotel_id,
                Services.status.in_(["pending", "in_progress"])
            )
            .group_by(Services.status)
            .all()
        )

        # inicia o dicionario com os status existentes
        summary = {"pending": 0, "in_progress": 0}

        # alimenta o dicionario com os valores retornados pela consulta e retorna
        for status, total in requests_by_status:
            summary[status] = total

        return summary

    # função que retorna os ultimos 3 pedidos não concluídos
    @staticmethod
    def get_recent_service_requests(db: Session, hotel_id: int, limit: int = 3):
        return (
            db.query(Services, Guest, Rooms)
            .join(Guest, Guest.id == Services.guest_id)
            .join(Rooms, Rooms.id == Services.room_id)
            .filter(
                Rooms.hotel_id == hotel_id,
                Services.status.in_(["pending", "in_progress"])
            )
            .order_by(Services.created_at.desc())
            .limit(limit)
            .all()
        )

    # ─── ATIVIDADE RECENTE ────────────────────────────────────────────────────

    #função que retorna as últimas 8 ações do registro de auditoria, exibido apenas para administradores
    @staticmethod
    def get_recent_activity(db: Session, hotel_id: int, limit: int = 8):
        return (
            db.query(AuditLog, Collaborator)
            .outerjoin(Collaborator, Collaborator.id == AuditLog.collaborator_id)
            .filter(AuditLog.hotel_id == hotel_id)
            .order_by(AuditLog.id.desc())
            .limit(limit)
            .all()
        )