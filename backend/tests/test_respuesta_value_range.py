import uuid

import pytest
from pydantic import ValidationError

from app.core.nit_utils import calcular_digito_verificador_nit
from app.schemas.common import RespuestaRequest


class TestRespuestaValorRangeSchema:
    def test_valor_valido_1(self):
        obj = RespuestaRequest(
            pregunta_codigo="PREGUNTA_001$",
            valor=1,
        )
        assert obj.valor == 1

    def test_valor_valido_5(self):
        obj = RespuestaRequest(
            pregunta_codigo="PREGUNTA_001$",
            valor=5,
        )
        assert obj.valor == 5

    def test_valor_valido_cero(self):
        obj = RespuestaRequest(
            pregunta_codigo="PREGUNTA_001$",
            valor=0,
        )
        assert obj.valor == 0

    def test_valor_invalido_seis(self):
        with pytest.raises(ValidationError):
            RespuestaRequest(
                pregunta_codigo="PREGUNTA_001$",
                valor=6,
            )

    def test_valor_invalido_negativo(self):
        with pytest.raises(ValidationError):
            RespuestaRequest(
                pregunta_codigo="PREGUNTA_001$",
                valor=-1,
            )


class TestRespuestaEndpointRange:
    def test_endpoint_rechaza_valor_fuera_de_rango_autenticado(self, client):
        res = client.post(
            "/api/auth/login",
            json={
                "email": "admin@magnussig.com",
                "password": "Admin1234",
            },
        )
        assert res.status_code == 200, res.text

        headers_admin = {
            "Authorization": f"Bearer {res.json()['token']}"
        }

        nit_base = f"9{str(uuid.uuid4().int)[:8]}"
        nit_rnd = (
            f"{nit_base}-"
            f"{calcular_digito_verificador_nit(nit_base)}"
        )

        res_org = client.post(
            "/api/organizaciones",
            headers=headers_admin,
            json={
                "nombre": "Empresa Test Likert SAS",
                "nit": nit_rnd,
            },
        )
        assert res_org.status_code in (200, 201), res_org.text
        org_id = res_org.json()["id"]

        email_eval = f"eval_likert_{uuid.uuid4().hex[:8]}@test.com"

        res_eval_user = client.post(
            "/api/usuarios",
            headers=headers_admin,
            json={
                "nombre": "Eva",
                "apellido": "Likert",
                "email": email_eval,
                "password": "Evaluador1234",
                "rolCodigo": "EVALUADOR_SST",
                "organizacionId": org_id,
            },
        )
        assert res_eval_user.status_code in (200, 201), res_eval_user.text

        res_login_eval = client.post(
            "/api/auth/login",
            json={
                "email": email_eval,
                "password": "Evaluador1234",
            },
        )
        assert res_login_eval.status_code == 200, res_login_eval.text

        headers_eval = {
            "Authorization": f"Bearer {res_login_eval.json()['token']}"
        }

        res_enlace = client.post(
            "/api/enlaces",
            headers=headers_eval,
            json={"nombre": "Prueba de rango Likert"},
        )
        assert res_enlace.status_code in (200, 201), res_enlace.text

        token_enlace = res_enlace.json()["token"]

        res_inicio = client.post(
            f"/api/enlaces/publico/{token_enlace}/iniciar",
            json={"aceptaConsentimiento": True},
        )
        assert res_inicio.status_code in (200, 201), res_inicio.text

        datos_inicio = res_inicio.json()
        token_participante = datos_inicio["token"]
        eval_id = datos_inicio["evaluacionId"]

        headers_participante = {
            "Authorization": f"Bearer {token_participante}"
        }

        res_preguntas = client.get(
            f"/api/evaluaciones/{eval_id}/cuestionario",
            headers=headers_participante,
        )
        assert res_preguntas.status_code == 200, res_preguntas.text

        preguntas = res_preguntas.json()["preguntas"]
        assert preguntas, "El cuestionario no contiene preguntas."

        pregunta_codigo = preguntas[0]["codigo"]

        assert pregunta_codigo, "La pregunta no tiene código."

        for valor in (6, 0):
            res_rechazo = client.post(
                f"/api/evaluaciones/{eval_id}/respuestas",
                headers=headers_participante,
                json={
                    "pregunta_codigo": pregunta_codigo,
                    "valor": valor,
                },
            )

            assert res_rechazo.status_code in (400, 422), (
                f"Se esperaba HTTP 400 o 422 para valor={valor}; "
                f"se recibió HTTP {res_rechazo.status_code}: "
                f"{res_rechazo.text}"
            )

        res_exitoso = client.post(
            f"/api/evaluaciones/{eval_id}/respuestas",
            headers=headers_participante,
            json={
                "pregunta_codigo": pregunta_codigo,
                "valor": 3,
            },
        )

        assert res_exitoso.status_code == 200, res_exitoso.text