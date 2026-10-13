import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.main import app as fastapi_app
from app.db.session import get_db
from app.core.config import get_settings
from app.core.crypto import hash_password
from app.db.base import Base
from app.models.user import Rol, Usuario
import app.models

from app.db.seed import (
    sembrar_permisos,
    sembrar_roles,
    sembrar_administrador,
    sembrar_cuestionario_brp,
)


settings = get_settings()
TEST_DATABASE_URL = settings.test_database_url

if not TEST_DATABASE_URL or "test" not in TEST_DATABASE_URL.lower():
    raise RuntimeError(
        f"ABORTANDO PRUEBAS: TEST_DATABASE_URL ('{TEST_DATABASE_URL}') "
        "no contiene la palabra 'test'. Para prevenir la eliminación "
        "accidental de datos de desarrollo o producción, las pruebas "
        "solo pueden ejecutarse contra una base de datos de prueba."
    )

engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    engine.dispose()

    # Comprobar la base antes de borrar cualquier objeto.
    with engine.begin() as conn:
        db_name = conn.execute(
            text("SELECT current_database()")
        ).scalar_one()

        if db_name != "magnussing_test":
            raise RuntimeError(
                f"Base incorrecta para pruebas: {db_name}"
            )

        # Reiniciar el esquema de la base EXCLUSIVA de pruebas.
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))

        # Crear las tablas según los modelos actuales.
        Base.metadata.create_all(bind=conn)

    db = TestingSessionLocal()

    try:
        permisos = sembrar_permisos(db)
        roles = sembrar_roles(db, permisos)
        sembrar_administrador(db, roles)
        sembrar_cuestionario_brp(db)
        db.commit()
    except Exception:
        db.rollback()
        raise
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
        yield db_session

    fastapi_app.dependency_overrides[get_db] = _override_get_db

    try:
        with TestClient(fastapi_app) as test_client:
            yield test_client
    finally:
        fastapi_app.dependency_overrides.clear()


@pytest.fixture
def crear_paciente(db_session):
    """
    Crea un usuario PACIENTE directamente en la base de pruebas.

    - Sin password: invitado (es_invitado=True), como los del enlace público.
    - Con password: paciente con login, útil para probar permisos por rol.

    Devuelve (usuario_id, email).
    """

    def _crear(organizacion_id, area_id=None, password=None):
        rol = db_session.query(Rol).filter(Rol.codigo == "PACIENTE").first()
        assert rol is not None, "El rol PACIENTE no está sembrado."

        email = f"paciente_{uuid.uuid4().hex[:10]}@test.com"
        usuario = Usuario(
            nombre="Paciente",
            apellido="Prueba",
            email=email,
            password_hash=hash_password(password or uuid.uuid4().hex),
            rol_id=rol.id,
            estado="ACTIVO",
            email_verificado=True,
            organizacion_id=uuid.UUID(str(organizacion_id)),
            area_id=uuid.UUID(str(area_id)) if area_id else None,
            es_invitado=password is None,
        )
        db_session.add(usuario)
        db_session.commit()
        db_session.refresh(usuario)
        return usuario.id, email

    return _crear