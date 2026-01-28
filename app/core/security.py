from itsdangerous import URLSafeTimedSerializer
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import os
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
serializer = URLSafeTimedSerializer(SECRET_KEY)

#CONFIGURAÇÃO DO CSRF (FORMS)
def generate_csrf_token():
    return serializer.dumps("csrf-token")

def validate_csrf_token(token, max_age=3600):
    try:
        serializer.loads(token, max_age=max_age)
        return True
    except Exception:
        return False
    
#CONFIGURAÇÃO DE HASH DA SENHA
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

#CONFIGURAÇÃO DE TOKEN JWT
#JWT PREPARADO PARA FUTURO USO EM INTEGRAÇÕES OU MICROSERVIÇOS
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
    
#API KEY HEADER CONFIGURATION
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

def get_api_key(api_key: str = Security(api_key_header)):
    if api_key == os.getenv("API_KEY"):
        return api_key
    else:
        raise HTTPException(status_code=403, detail="API Key não autorizada.")