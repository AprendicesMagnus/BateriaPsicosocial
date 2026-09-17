import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.session import get_db
from app.core.config import get_settings
from app.db.base import Base
from app.db.seed import sembrar_permisos, sembrar_roles, sembrar_administrador, sembrar_cuestionario_brp

settings = get_settings()
TEST_DATABASE_URL = settings.test_database_url

if "test" not in TEST_DATABASE_URL.lower():
    raise RuntimeError(
        f"ABORTANDO PRUEBAS: TEST_DATABASE_URL ('{TEST_DATABASE_URL}') no contiene la palabra 'test'. "
        "Para prevenir la eliminación accidental de datos de producción o desarrollo, las pruebas solo "
        "pueden ejecutarse contra una base de datos de prueba (ej: magnussing_test)."
    )

engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    engine.dispose()
    with engine.begin() as conn:
        Base.metadata.drop_all(bind=conn)
        Base.metadata.create_all(bind=conn)
    db = TestingSessionLocal()
    try:
        permisos = sembrar_permisos(db)
        roles = sembrar_roles(db, permisos)
        sembrar_administrador(db, roles)
        sembrar_cuestionario_brp(db)
        db.commit()
    finally:
        db.close()
    yield
    engine.dispose()

@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def client(db_session):
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
