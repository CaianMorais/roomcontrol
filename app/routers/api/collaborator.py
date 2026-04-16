# import de libs padrão
from typing import List, Optional

# import de libs third-party
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session

# import do current-app
from app.core.config import get_db
from app.core.dependencies import get_api_access
from app.schemas.collaborator import CollaboratorOut
from app.services.collaborator_service import ApiCollaboratorService

# configuração do router
api_router = APIRouter(
    prefix="/api",
    tags=["collaborators"],
    dependencies=[Depends(get_api_access)]
)

@api_router.get("/collaborators", response_model=List[CollaboratorOut], summary="Filtrar colaboradores (Exclusivo para chave global)")
def get_collaborators(
    access: dict = Depends(get_api_access),
    hotel_name: Optional[str] = Query(None, description="Filtrar pelo nome do hotel"),
    firstname: Optional[str] = Query(None, description="Filtrar pelo primeiro nome"),
    lastname: Optional[str] = Query(None, description="Filtrar pelo último nome"),
    cpf: Optional[str] = Query(None, description="Filtrar pelo CPF"),
    db: Session = Depends(get_db)
):
    if not access["is_global"]:
        raise HTTPException(status_code=403, detail="API Key não autorizada")

    query = ApiCollaboratorService.list_collaborators(db)

    if hotel_name or firstname or lastname or cpf:
        print("Aplicando filtros na consulta de colaboradores...")
        query = ApiCollaboratorService.filter_collaborators(query, hotel_name, firstname, lastname, cpf)

    collaborators = query.all()

    if not collaborators:
        collaborators = []

    return collaborators