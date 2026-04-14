from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
from app.core.config import SessionLocal
from app.utils.flash import add_flash_message
from app.models.hotel import Hotel
from app.models.collaborator import Collaborator
from fastapi import Depends


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# def require_session(request: Request, db=Depends(get_db)):
#     hotel_id = request.session.get("hotel_id")
#     hotel_name = request.session.get("hotel_name")
#     collaborator_id = request.session.get("collaborator_id")

#     if not hotel_id:
#         add_flash_message(request, "Faça login para acessar o painel", "warning")
#         raise HTTPException(status_code=307, headers={"Location": ""})
    
#     if not db.query(Hotel).filter(Hotel.id == hotel_id).filter(Hotel.is_active == True).first():
#         request.session.clear()
#         add_flash_message(request, "Seu hotel foi desativado, ou não existe mais. Caso necessário, entre em contato com o suporte.", "danger")
#         raise HTTPException(status_code=307, headers={"Location": ""})
    
#     return {"id": hotel_id, "name": hotel_name}

def require_admin_session(
    request: Request,
    db=Depends(get_db)
):
    hotel_id = request.session.get("hotel_id")
    collaborator_id = request.session.get("collaborator_id")

    if not hotel_id or collaborator_id:
        add_flash_message(request, "Sem permissão", "danger")
        raise HTTPException(status_code=307, headers={"Location": "/auth/hotel"})

    hotel = db.query(Hotel).filter(
        Hotel.id == hotel_id,
        Hotel.is_active == True
    ).first()

    if not hotel:
        request.session.clear()
        add_flash_message(request, "Autenticação necessária", "danger")
        raise HTTPException(status_code=307, headers={"Location": "/auth/hotel"})

    return hotel

def require_collaborator_session(
    request: Request,
    db=Depends(get_db)
):
    hotel_id = request.session.get("hotel_id")
    collaborator_id = request.session.get("collaborator_id")

    if not hotel_id or not collaborator_id:
        add_flash_message(request, "Autenticação necessária", "danger")
        raise HTTPException(status_code=307, headers={"Location": "/auth/collaborator"})

    collaborator = db.query(Collaborator).filter(
        Collaborator.id == collaborator_id,
        Collaborator.hotel_id == hotel_id,
        Collaborator.is_active == True,
        Collaborator.is_deleted == False
    ).first()

    if not collaborator:
        request.session.clear()
        add_flash_message(request, "Autenticação necessária", "danger")
        raise HTTPException(status_code=303, headers={"Location": "/auth/collaborator"})

    return collaborator

def require_session(request: Request, db=Depends(get_db)):
    # as rotas que podem ser acessadas por colaborador e administrador
    # passa por aqui para validar se a sessão do colaborador ou hotel é valida
    # tambem permite que as rotas dependentes de require_session possam ser acessadas por ambos
    if not request.session.get("hotel_id"):
        add_flash_message(request, "Autenticação necessária", "danger")
        raise HTTPException(status_code=303, headers={"Location": "/"})
    
    collaborator_id = request.session.get("collaborator_id")
    admin_logged_in = request.session.get("admin_logged_in")
    if collaborator_id:
        return require_collaborator_session(request, db)
    elif admin_logged_in:
        return require_admin_session(request, db)
    else:
        raise HTTPException(status_code=303, headers={"Location": "/"})