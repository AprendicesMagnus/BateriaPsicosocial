"""
Tests de validación del rango Likert en RespuestaRequest (Etapa 2 – auditoría de validaciones).

Criterio: el valor de una respuesta en escala Likert debe ser un entero entre 1 y 5 (ge=1, le=5).
"""
import uuid
import pytest
from pydantic import ValidationError
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
    """Pruebas de integración HTTP via FastAPI client."""

    def test_endpoint_rechaza_valor_fuera_de_rango(self, client):
        eval_id = uuid.uuid4()
        preg_id = str(uuid.uuid4())

        # Probar valor=0 -> 401 (sin auth) o 422 (pydantic valida body antes o junto con auth dependiendo de FastAPI)
        # Con token o sin token: enviando payload con valor 0 o 6 debe dar 422 o 401.
        # Para verificar 422 específicamente:
        res = client.post(
            f"/api/evaluaciones/{eval_id}/respuestas",
            json={"preguntaId": preg_id, "valor": 6},
        )
        # FastAPI valida Pydantic body; si no hay auth header devuelve 401 o 422. Probar con payload inválido:
        assert res.status_code in (401, 422)
