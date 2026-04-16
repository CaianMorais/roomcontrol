# import de libs third-party
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

# import do current-app
from app.core.config import get_db
from app.core.dependencies import get_api_access
from app.services.audit_service import AuditService


# configuração do router
api_router = APIRouter(
    prefix="/api",
    tags=["audit_logs"],
    dependencies=[Depends(get_api_access)]
)

############## API (ENDPOINTS) ################
# ENDPOINT PRÉ EXISTENTE PARA CASO FUTURO
@api_router.get("/audit")
def get_audit_logs(
    db: Session = Depends(get_db)
):
    keys = AuditService.list_logs(db)

    if not keys:
        keys = []

    return keys