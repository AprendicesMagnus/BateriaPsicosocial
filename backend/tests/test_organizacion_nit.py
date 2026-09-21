r"""
Tests de validación del NIT completo con Dígito de Verificación (DV) Módulo 11 DIAN.

Formato requerido: `NNNNNNNNN-D` (9 dígitos base, guion, 1 dígito verificador).
Validación en 2 niveles:
1. Schema Pydantic / Query parameter: `pattern=r"^\d{9}-\d$"` (error 422 si el formato no coincide).
2. Capa de servicio: `calcular_digito_verificador_nit(base) == dv` (error 400 AppError con mensaje específico si el DV no coincide).
"""

from app.core.nit_utils import calcular_digito_verificador_nit

# ─── helpers ───────────────────────────────────────────────────────────────────

# ECOPETROL S.A.: 899999068-1 (DV real 1)
NIT_VALIDO_REAL = "899999068-1"

AUTORREGISTRO_BASE = {
    "nit": NIT_VALIDO_REAL,
    "nombre": "Empresa Test DV",
    "usuarioNombre": "Juan",
    "usuarioApellido": "Pérez",
    "usuarioEmail": "jperez_dv@test.com",
    "usuarioPassword": "Abc12345",
}


def _autorregistro(client, nit: str) -> int:
    payload = {**AUTORREGISTRO_BASE, "nit": nit}
    return client.post("/api/organizaciones/autorregistro", json=payload).status_code


def _existe_get(client, nit: str) -> int:
    return client.get(f"/api/organizaciones/existe?nit={nit}").status_code


# ─── GET /organizaciones/existe ─────────────────────────────────────────────────

class TestExisteNitQueryParam:
    """GET /organizaciones/existe — validación del formato NNNNNNNNN-D."""

    def test_nit_formato_valido_con_dv(self, client):
        assert _existe_get(client, "899999068-1") == 200

    def test_nit_sin_guion_formato_invalido(self, client):
        assert _existe_get(client, "899999068") == 422

    def test_nit_menos_de_9_digitos_base(self, client):
        assert _existe_get(client, "12345678-1") == 422

    def test_nit_mas_de_9_digitos_base(self, client):
        assert _existe_get(client, "1234567890-1") == 422

    def test_nit_con_letras(self, client):
        assert _existe_get(client, "12345678a-1") == 422

    def test_nit_vacio(self, client):
        assert _existe_get(client, "") == 422


# ─── POST /organizaciones/autorregistro — Integración End-to-End DV ─────────────

class TestNitAutorregistroConDigitoVerificador:
    """Pruebas end-to-end de validación de NIT y Dígito de Verificación (DV)."""

    def test_nit_con_dv_correcto_exitoso(self, client):
        # BANCO DE BOGOTA S.A.: 860003020-1 (DV real = 1)
        payload = {**AUTORREGISTRO_BASE, "nit": "860003020-1", "usuarioEmail": "banco_test@test.com"}
        res = client.post("/api/organizaciones/autorregistro", json=payload)
        assert res.status_code == 200

    def test_nit_con_dv_incorrecto_rechazo_especifico_400(self, client):
        # 899999068 tiene DV real = 1. Se envía 899999068-9 (DV incorrecto)
        payload = {**AUTORREGISTRO_BASE, "nit": "899999068-9", "usuarioEmail": "dv_incorrecto@test.com"}
        res = client.post("/api/organizaciones/autorregistro", json=payload)
        assert res.status_code == 400
        data = res.json()
        assert "dígito de verificación" in str(data).lower()

    def test_nit_sin_guion_rechazo_schema_422(self, client):
        assert _autorregistro(client, "899999068") == 422

    def test_nit_con_letras_rechazo_schema_422(self, client):
        assert _autorregistro(client, "ABCDEFGHI-1") == 422

    def test_nit_vacio_rechazo_schema_422(self, client):
        assert _autorregistro(client, "") == 422
