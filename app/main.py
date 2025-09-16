from fastapi import FastAPI, HTTPException, Request, Form, Depends
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from validate_docbr import CPF
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import Base, engine, SessionLocal
from app.models.guest import Guest
from app.core.security import validate_csrf_token, generate_csrf_token
from app.routers import auth, guest

#criar tabelas
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Hotel Management API")

templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

#criptografia das sessões
app.add_middleware(SessionMiddleware, secret_key="roomcontrolsecretkey")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app.include_router(auth.router)
app.include_router(guest.router)

@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    guests = db.query(Guest).all()
    return templates.TemplateResponse("index.html", {"request": request, "guests": guests})

# handler para erros HTTP (inclui 404, 403, 400 etc.)
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "status_code": exc.status_code,
            "detail": exc.detail if exc.detail else "Erro desconhecido."
        },
        status_code=exc.status_code,
    )

# handler para erros internos (500 e outros não tratados)
@app.exception_handler(Exception)
async def internal_exception_handler(request: Request, exc: Exception):
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "status_code": 500,
            "detail": "Erro interno do servidor. Tente novamente mais tarde."
        },
        status_code=500,
    )