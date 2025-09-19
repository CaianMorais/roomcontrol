from app.core.config import SessionLocal
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Form, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from passlib.hash import bcrypt

from app.utils.flash import render
from app.utils.session_guard import require_session

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
    dependencies=[Depends(require_session)]
)

api_router = APIRouter(prefix="/api", tags=["api_dashboard"])
templates = Jinja2Templates(directory="app/templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("", response_class=HTMLResponse, include_in_schema=False)
def dashboard(request: Request):
    ctx = {
        "hotel_name": request.session.get("hotel_name"),
        "hotel_id": request.session.get("hotel_id")
    }
    return render(
        templates,
        request,
        "/dashboard/index.html",
        ctx
    )
