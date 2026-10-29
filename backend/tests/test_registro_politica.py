import uuid

import pytest

from app.models.user import Usuario
from app.models.audit import Auditoria
from app.services import auth as auth_service

BASE_PAYLOAD = {
    "nombre": "Laura",
    "apellido": "Gomez",
    "password": "Password123",
    "rol": "JEFE",
}


def _email():
    return f"laura_{uuid.uuid4().hex[:10]}@test.com"


def _google_payload(email):
    return {
        "email": email,
        "email_verified": True,
        "given_name": "Laura",
        "family_name": "Gomez",
    }


def test_registro_sin_aceptar_politica_es_rechazado(client):
    email = _email()
    payload = {**BASE_PAYLOAD, "email": email}
    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 400, res.text
    assert "política" in res.json().get("error", "").lower() or "politica" in res.json().get("error", "").lower()


def test_registro_con_politica_en_false_es_rechazado(client, db_session):
    email = _email()
    payload = {**BASE_PAYLOAD, "email": email, "aceptaPolitica": False}
    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 400, res.text
    usuario = db_session.query(Usuario).filter(Usuario.email == email).first()
    assert usuario is None, "No se debe crear el usuario si rechaza la politica"


def test_registro_con_politica_guarda_version_fecha_y_auditoria(client, db_session):
    email = _email()
    payload = {**BASE_PAYLOAD, "email": email, "aceptaPolitica": True}
    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 200, res.text

    usuario = db_session.query(Usuario).filter(Usuario.email == email).first()
    assert usuario is not None
    assert usuario.politica_version == "1.0"
    assert usuario.politica_aceptada_en is not None

    auditoria = (
        db_session.query(Auditoria)
        .filter(
            Auditoria.usuario_id == usuario.id,
            Auditoria.accion == "POLITICA_ACEPTADA",
        )
        .first()
    )
    assert auditoria is not None, "Debe existir un registro de auditoria POLITICA_ACEPTADA"
    assert auditoria.nota == "Versión 1.0"


def test_google_cuenta_nueva_sin_rol_no_crea_ni_pide_politica(client, db_session, monkeypatch):
    email = _email()
    payload = _google_payload(email)
    monkeypatch.setattr(
        auth_service.google_id_token,
        "verify_oauth2_token",
        lambda *args, **kwargs: payload,
    )
    res = client.post("/api/auth/google", json={"credential": "x" * 30})
    assert res.status_code == 200, res.text
    assert res.json().get("requiereRol") is True
    usuario = db_session.query(Usuario).filter(Usuario.email == email).first()
    assert usuario is None, "No se debe crear el usuario cuando falta el rol"


def test_google_cuenta_nueva_sin_aceptar_es_rechazada(client, db_session, monkeypatch):
    email = _email()
    payload = _google_payload(email)
    monkeypatch.setattr(
        auth_service.google_id_token,
        "verify_oauth2_token",
        lambda *args, **kwargs: payload,
    )
    res = client.post("/api/auth/google", json={"credential": "x" * 30, "rol": "JEFE"})
    assert res.status_code == 400, res.text
    usuario = db_session.query(Usuario).filter(Usuario.email == email).first()
    assert usuario is None, "No se debe crear el usuario si rechaza la politica"


def test_google_cuenta_nueva_con_politica_guarda_version_y_auditoria(client, db_session, monkeypatch):
    email = _email()
    payload = _google_payload(email)
    monkeypatch.setattr(
        auth_service.google_id_token,
        "verify_oauth2_token",
        lambda *args, **kwargs: payload,
    )
    res = client.post(
        "/api/auth/google",
        json={"credential": "x" * 30, "rol": "JEFE", "aceptaPolitica": True},
    )
    assert res.status_code == 200, res.text
    assert "token" in res.json()

    usuario = db_session.query(Usuario).filter(Usuario.email == email).first()
    assert usuario is not None
    assert usuario.politica_version == "1.0"
    assert usuario.politica_aceptada_en is not None

    auditoria = (
        db_session.query(Auditoria)
        .filter(
            Auditoria.usuario_id == usuario.id,
            Auditoria.accion == "POLITICA_ACEPTADA",
        )
        .first()
    )
    assert auditoria is not None, "Debe existir un registro de auditoria POLITICA_ACEPTADA"
    assert auditoria.nota == "Versión 1.0"


def test_google_cuenta_existente_entra_sin_politica_y_no_duplica_auditoria(client, db_session, monkeypatch):
    email = _email()
    payload = _google_payload(email)
    monkeypatch.setattr(
        auth_service.google_id_token,
        "verify_oauth2_token",
        lambda *args, **kwargs: payload,
    )

    # Primera llamada: crea la cuenta
    res1 = client.post(
        "/api/auth/google",
        json={"credential": "x" * 30, "rol": "JEFE", "aceptaPolitica": True},
    )
    assert res1.status_code == 200, res1.text

    usuario = db_session.query(Usuario).filter(Usuario.email == email).first()
    assert usuario is not None
    auditorias_tras_crear = (
        db_session.query(Auditoria)
        .filter(Auditoria.usuario_id == usuario.id, Auditoria.accion == "POLITICA_ACEPTADA")
        .count()
    )
    assert auditorias_tras_crear == 1

    # Segunda llamada: cuenta ya existe, solo entra, sin enviar aceptaPolitica
    res2 = client.post("/api/auth/google", json={"credential": "x" * 30})
    assert res2.status_code == 200, res2.text
    assert "token" in res2.json()

    db_session.expire_all()
    auditorias_tras_reentrar = (
        db_session.query(Auditoria)
        .filter(Auditoria.usuario_id == usuario.id, Auditoria.accion == "POLITICA_ACEPTADA")
        .count()
    )
    assert auditorias_tras_reentrar == 1, "No debe duplicar la auditoria POLITICA_ACEPTADA al volver a entrar"
