import os
from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.utils.flash import add_flash_message, render
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import SessionLocal
from app.models.guest import Guest
from app.routers import auth, guest

app = FastAPI(title="Hotel Management API")

templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static/main"), name="static")
app.mount("/dashboard", StaticFiles(directory="app/static/dashboard"), name="dashboard")

#criptografia das sessões
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "your_secret_key"))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app.include_router(auth.api_router)
app.include_router(guest.api_router)
app.include_router(auth.router)
app.include_router(guest.router)

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def home(request: Request, db: Session = Depends(get_db)):
    guests = db.query(Guest).all()
    #return templates.TemplateResponse("index.html", {"request": request, "guests": guests})
    return render(templates, request, "index.html", {"request": request, "guests": guests})

# Handler para erros HTTP
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail if exc.detail else "Erro desconhecido."}
        )
    else:
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