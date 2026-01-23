import os
import json
import base64
import pytest
from itsdangerous import TimestampSigner
from dotenv import load_dotenv

# Carrega env de teste primeiro
load_dotenv(".env.test", override=True)

TEST_DB_URL = os.getenv("TEST_DATABASE_URL")
if not TEST_DB_URL:
    raise RuntimeError("Defina TEST_DATABASE_URL no .env.test")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app as fastapi_app
from app.core.config import Base
from app.core.config import get_db as project_get_db

load_dotenv(".env.test", override=False)

TEST_DB_URL = os.getenv("TEST_DATABASE_URL")
if not TEST_DB_URL:
    raise RuntimeError("Defina TEST_DATABASE_URL (ex.: em .env.test) para apontar para o MySQL de testes.")


@pytest.fixture(scope="session")
def engine():
    eng = create_engine(TEST_DB_URL, pool_pre_ping=True)

    # cria schema baseado nos models
    Base.metadata.drop_all(bind=eng)
    Base.metadata.create_all(bind=eng)
    yield eng

    # limpar tudo ao final
    Base.metadata.drop_all(bind=eng)


@pytest.fixture()
def db_session(engine):
    connection = engine.connect()
    trans = connection.begin()
    TestingSessionLocal = sessionmaker(bind=connection, autoflush=False, autocommit=False)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        trans.rollback()
        connection.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    # sobrescreve o get_db ORIGINAL
    fastapi_app.dependency_overrides[project_get_db] = override_get_db

    with TestClient(fastapi_app) as c:
        yield c

    fastapi_app.dependency_overrides.clear()


def set_session_cookie(client: TestClient, session_dict: dict, secret_key: str | None = None):
    #função necessário para setar cookies no início da sessão, caso exija hotel_id ou outro dado na sessão
    secret_key = secret_key or os.getenv("SECRET_KEY", "test-secret")
    signer = TimestampSigner(secret_key, salt="starlette.sessions")

    payload = base64.b64encode(json.dumps(session_dict).encode("utf-8")).decode("utf-8")
    signed = signer.sign(payload).decode("utf-8")
    client.cookies.set("session", signed)
