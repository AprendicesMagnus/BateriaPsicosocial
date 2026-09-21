"""
Tests de validación del rango Likert en RespuestaRequest (Etapa 2 – auditoría de validaciones).

Criterio: el valor de una respuesta en escala Likert debe ser un entero entre 1 y 5 (ge=1, le=5).
"""
import uuid
import pytest
from pydantic import ValidationError
from app.core.nit_utils import calcular_digito_verificador_nit
from app.schemas.common import RespuestaRequest


class TestRespuestaValorRangeSchema:
    """Pruebas unitarias directas del schema Pydantic RespuestaRequest."""

    def test_valor_valido_1(self):
        obj = RespuestaRequest(preguntaId=uuid.uuid4(), valor=1)
        assert obj.valor == 1

    def test_valor_valido_5(self):
        obj = RespuestaRequest(preguntaId=uuid.uuid4(), valor=5)
        assert obj.valor == 5

    def test_valor_invalido_cero(self):
        with pytest.raises(ValidationError):
            RespuestaRequest(preguntaId=uuid.uuid4(), valor=0)

    def test_valor_invalido_seis(self):
        with pytest.raises(ValidationError):
            RespuestaRequest(preguntaId=uuid.uuid4(), valor=6)

    def test_valor_invalido_negativo(self):
        with pytest.raises(ValidationError):
            RespuestaRequest(preguntaId=uuid.uuid4(), valor=-1)


class TestRespuestaEndpointRange:
    """Pruebas de integración HTTP autenticadas via FastAPI client."""

    def test_endpoint_rechaza_valor_fuera_de_rango_autenticado(self, client):
        # 1. Login admin
        res = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
        assert res.status_code == 200
        headers_admin = {"Authorization": f"Bearer {res.json()['token']}"}

        # 2. Crear Org, Area, Trabajador y Evaluacion
        nit_base = f"9{str(uuid.uuid4().int)[:8]}"
        nit_rnd = f"{nit_base}-{calcular_digito_verificador_nit(nit_base)}"
        res_org = client.post("/api/organizaciones", headers=headers_admin, json={
            "nombre": "Empresa Test Likert SAS",
            "nit": nit_rnd,
        })
        org_id = res_org.json()["id"]

        res_area = client.post("/api/organizaciones/areas", headers=headers_admin, json={
            "organizacionId": org_id,
            "nombre": "TI Likert"
        })
        area_id = res_area.json()["id"]

        email_trab = f"trab_likert_{uuid.uuid4().hex[:5]}@test.com"
        res_trab = client.post("/api/usuarios", headers=headers_admin, json={
            "nombre": "Luis",
            "apellido": "Likert",
            "email": email_trab,
            "password": "Trabajador1234",
            "rolCodigo": "TRABAJADOR",
            "organizacionId": org_id,
            "areaId": area_id,
            "numeroIdentificacion": f"{str(uuid.uuid4().int)[:10]}",
            "cargo": "Analista"
        })
        trabajador_id = res_trab.json()["id"]

        version_id = client.get("/api/cuestionarios", headers=headers_admin).json()[0]["id"]
        res_eval = client.post("/api/evaluaciones", headers=headers_admin, json={
            "organizacionId": org_id,
            "nombre": "Evaluacion Likert 2026",
            "versionId": version_id,
            "trabajadoresIds": [trabajador_id]
        })
        eval_id = res_eval.json()["id"]

        client.post(f"/api/evaluaciones/{eval_id}/iniciar", headers=headers_admin)

        # 3. Login Trabajador y consentimiento
        res_login_trab = client.post("/api/auth/login", json={"email": email_trab, "password": "Trabajador1234"})
        headers_trab = {"Authorization": f"Bearer {res_login_trab.json()['token']}"}
        client.post(f"/api/evaluaciones/{eval_id}/consentimiento", headers=headers_trab)

        preguntas = client.get(f"/api/evaluaciones/{eval_id}/cuestionario", headers=headers_trab).json()["preguntas"]
        pregunta_id = preguntas[0]["id"]

        # 4. Probar envío de valor=6 autenticado -> debe retornar 422 específicamente por Pydantic validation
        res_rechazo_6 = client.post(
            f"/api/evaluaciones/{eval_id}/respuestas",
            headers=headers_trab,
            json={"preguntaId": pregunta_id, "valor": 6},
        )
        assert res_rechazo_6.status_code == 422

        # Probar valor=0 -> 422
        res_rechazo_0 = client.post(
            f"/api/evaluaciones/{eval_id}/respuestas",
            headers=headers_trab,
            json={"preguntaId": pregunta_id, "valor": 0},
        )
        assert res_rechazo_0.status_code == 422

        # Probar valor=3 -> 200 (caso feliz)
        res_exitoso = client.post(
            f"/api/evaluaciones/{eval_id}/respuestas",
            headers=headers_trab,
            json={"preguntaId": pregunta_id, "valor": 3},
        )
        assert res_exitoso.status_code == 200
