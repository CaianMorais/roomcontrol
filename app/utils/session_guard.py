from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
from app.utils.flash import add_flash_message

def require_session(request: Request):
    hotel_id = request.session.get("hotel_id")
    hotel_name = request.session.get("hotel_name")

    if not hotel_id:
        add_flash_message(request, "Faça login para acessar o painel", "warning")
        raise HTTPException(status_code=307, headers={"Location": "/auth"})
    
    return {"id": hotel_id, "name": hotel_name}