import os
import uvicorn
from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_pagination import add_pagination
from utils.flash import render
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from core.config import SessionLocal
from models.guest import Guest
from routers import auth, guest, dashboard, dashboard_rooms, dashboard_guests, dashboard_reservations, dashboard_services

app = FastAPI(title="Room Control - API de Gerenciamento")

templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static/main"), name="static")
app.mount("/dashboard", StaticFiles(directory="app/static/dashboard"), name="dashboard")
app.mount("/guests_access", StaticFiles(directory='app/static/guests_access'), name="guests_access")

#criptografia das sessões
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "your_secret_key"))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

add_pagination(app)

#INCLUSAO DAS ROTAS DE API
app.include_router(auth.api_router)
app.include_router(guest.api_router)
app.include_router(dashboard.api_router)
app.include_router(dashboard_rooms.api_router)
app.include_router(dashboard_guests.api_router)
app.include_router(dashboard_reservations.api_router)
app.include_router(dashboard_services.api_router)

#INCLUSAO DAS ROTAS DE PAGINAS
app.include_router(auth.router)
app.include_router(guest.router)
app.include_router(dashboard.router)
app.include_router(dashboard_rooms.router)
app.include_router(dashboard_guests.router)
app.include_router(dashboard_reservations.router)
app.include_router(dashboard_services.router)

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def home(request: Request, db: Session = Depends(get_db)):
    guests = db.query(Guest).all()
    #return templates.TemplateResponse("index.html", {"request": request, "guests": guests})
    return render(templates, request, "index.html", {"request": request, "guests": guests})


REDIRECT_STATUSES = {301, 302, 303, 307, 308}

# Handler para erros HTTP
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    # Se for código de redirect, respeite o Location
    if exc.status_code in REDIRECT_STATUSES:
        location = exc.headers.get("Location") if exc.headers else None
        if location:
            return RedirectResponse(url=location, status_code=exc.status_code)
        
    # Se for erro pela API, resposta em JSON
    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail if exc.detail else "Erro desconhecido."}
        )
    
    # página de erro
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "status_code": exc.status_code,
            "detail": exc.detail if exc.detail else "Erro desconhecido."
        },
        status_code=exc.status_code,
    )

# Handler para erros internos
@app.exception_handler(Exception)
async def internal_exception_handler(request: Request, exc: Exception):
    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=500,
            content={"detail": "Erro interno do servidor. Tente novamente mais tarde."}
        )
    else:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "status_code": 500,
                "detail": "Erro interno do servidor. Tente novamente mais tarde."
            },
            status_code=500,
        )
    
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)