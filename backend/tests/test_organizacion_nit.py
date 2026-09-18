"""
Tests de validación de NIT (Etapa 1 – auditoría de validaciones).

Criterio: el NIT debe ser exactamente 9 dígitos numéricos (r'^\\d{9}$').
No se valida dígito verificador — solo longitud y contenido numérico.
"""

# ─── helpers ───────────────────────────────────────────────────────────────────

AUTORREGISTRO_BASE = {
    "nit": "123456789",
    "nombre": "Empresa Test",
    "usuarioNombre": "Juan",
    "usuarioApellido": "Pérez",
    "usuarioEmail": "jperez@test.com",
    "usuarioPassword": "Abc12345",
}


def _autorregistro(client, nit: str) -> int:
    payload = {**AUTORREGISTRO_BASE, "nit": nit}
    return client.post("/api/organizaciones/autorregistro", json=payload).status_code


def _existe_get(client, nit: str) -> int:
    return client.get(f"/api/organizaciones/existe?nit={nit}").status_code


# ─── GET /organizaciones/existe ─────────────────────────────────────────────────

class TestExisteNitQueryParam:
    """GET /organizaciones/existe — validación del query-param."""

    def test_nit_valido_9_digitos(self, client):
        assert _existe_get(client, "123456789") == 200

    def test_nit_menos_de_9_digitos(self, client):
        assert _existe_get(client, "12345678") == 422

    def test_nit_mas_de_9_digitos(self, client):
        assert _existe_get(client, "1234567890") == 422

    def test_nit_con_letras(self, client):
        assert _existe_get(client, "12345678a") == 422

    def test_nit_vacio(self, client):
        assert _existe_get(client, "") == 422

    def test_nit_con_guion(self, client):
        assert _existe_get(client, "123-45678") == 422


# ─── POST /organizaciones/autorregistro ─────────────────────────────────────────

class TestNitAutorregistro:
    """POST /organizaciones/autorregistro — validación del campo nit."""

    def test_nit_valido_9_digitos(self, client):
        # NIT único para que no haya conflicto con otros tests
        payload = {**AUTORREGISTRO_BASE, "nit": "987654321", "usuarioEmail": "a@a.com"}
        assert client.post("/api/organizaciones/autorregistro", json=payload).status_code == 200

    def test_nit_menos_de_9_digitos(self, client):
        assert _autorregistro(client, "12345678") == 422

    def test_nit_mas_de_9_digitos(self, client):
        assert _autorregistro(client, "1234567890") == 422

    def test_nit_con_letras(self, client):
        assert _autorregistro(client, "ABCDEFGHI") == 422

    def test_nit_vacio(self, client):
        assert _autorregistro(client, "") == 422
