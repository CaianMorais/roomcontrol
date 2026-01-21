from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
from app.core.config import SessionLocal
from app.utils.flash import add_flash_message
from app.models.hotel import Hotel
from fastapi import Depends


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def require_session(request: Request, db=Depends(get_db)):
    hotel_id = request.session.get("hotel_id")
    hotel_name = request.session.get("hotel_name")

    if not hotel_id:
        add_flash_message(request, "Faça login para acessar o painel", "warning")
        raise HTTPException(status_code=307, headers={"Location": "/auth"})
    
    if not db.query(Hotel).filter(Hotel.id == hotel_id).filter(Hotel.is_active == True).first():
        request.session.clear()
        add_flash_message(request, "Seu hotel foi desativado, ou não existe mais. Caso necessário, entre em contato com o suporte.", "danger")
        raise HTTPException(status_code=307, headers={"Location": "/auth"})
    
    return {"id": hotel_id, "name": hotel_name}