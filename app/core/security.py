import secrets
from itsdangerous import URLSafeTimedSerializer
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import os
from fastapi import Security, HTTPException, Depends, Request
from fastapi.security import APIKeyHeader, HTTPBasic, HTTPBasicCredentials

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
serializer = URLSafeTimedSerializer(SECRET_KEY)

#CONFIGURAÇÃO DO CSRF (FORMS)
def generate_csrf_token(request: Request):
    token = secrets.token_urlsafe(32)
    request.session["csrf_token"] = token
    return token

def validate_csrf_token(request: Request, token: str):
    session_token = request.session.get("csrf_token")

    if not session_token:
        return False

    return secrets.compare_digest(session_token, token)
    
#CONFIGURAÇÃO DE HASH DA SENHA
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
    
# AUTENTICAÇÃO PARA ACESSAR O /DOCS
security = HTTPBasic()

def docs_auth(credentials: HTTPBasicCredentials = Depends(security)):
    correct_user = secrets.compare_digest(
        credentials.username,
        os.getenv("DOCS_USERNAME")
    )
    correct_pass = secrets.compare_digest(
        credentials.password,
        os.getenv("DOCS_PASSWORD")
    )

    if not (correct_user and correct_pass):
        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Basic"},
        )

    return credentials.username