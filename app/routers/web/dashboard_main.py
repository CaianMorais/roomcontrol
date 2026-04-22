from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.config import get_db
from app.services.main_service import MainService
from app.utils.flash import render
from app.utils.session_guard import require_session

#configuração do router e templates
router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
    dependencies=[Depends(require_session)]
)
templates = Jinja2Templates(directory="app/templates")


@router.get("", response_class=HTMLResponse, include_in_schema=False)
def dashboard(
    request: Request,
    db: Session = Depends(get_db)
):

    hotel_id = request.session.get("hotel_id")

    rooms = MainService.get_rooms_summary(db, hotel_id)
    reservations = MainService.get_reservations_summary(db, hotel_id)

    if not request.session.get("collaborator_id"):
        activity = MainService.get_recent_activity(db, hotel_id)
    else:
        activity = []  # colaboradores não veem atividade recente, só administradores

    return render(
        templates,
        request,
        "dashboard/main/dashboard.html",
        {
            "rooms": rooms,
            "reservations": reservations,
            "activity": activity,
        }
    )

