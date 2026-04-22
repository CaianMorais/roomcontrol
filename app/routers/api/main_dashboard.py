#import de libs third-party
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

# import de funções da aplicação local
from app.core.config import get_db
from app.services.main_service import MainService
from app.utils.session_guard import require_session

# internal_api_router:
# usado pelo JS do dashboard para buscar dados sem recarregar a página
internal_api_router = APIRouter(
    prefix="/internal_api/dashboard",
    tags=["dashboard"],
    dependencies=[Depends(require_session)]
)

# api_router = APIRouter(
#     prefix="/api",
#     tags=["api_dashboard"]
# )

@internal_api_router.get("/services", include_in_schema=False)
def get_services_data(request: Request, db: Session = Depends(get_db)):
    hotel_id = request.session.get("hotel_id")
    return JSONResponse({
        "summary": MainService.get_services_summary(db, hotel_id),
        "requests": MainService.get_recent_service_requests(db, hotel_id),
    })


@internal_api_router.get("/upcoming_checkins", include_in_schema=False)
def get_upcoming_checkins(request: Request, db: Session = Depends(get_db)):
    hotel_id = request.session.get("hotel_id")
    return JSONResponse({
        "checkins": MainService.get_upcoming_checkins(db, hotel_id),
    })