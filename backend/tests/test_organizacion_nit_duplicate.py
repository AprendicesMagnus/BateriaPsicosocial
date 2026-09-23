"""
Tests de duplicado de NIT en POST /api/organizaciones/autorregistro.

NIT usado: 123456789-6 (base 123456789, dígito verificador real = 6).
Email de usuario único para no chocar con otros tests.
"""

NIT_DUPLICADO = "123456789-6"

PAYLOAD_BASE = {
    "nit": NIT_DUPLICADO,
    "nombre": "Empresa Duplicada Test",
    "usuarioNombre": "Ana",
    "usuarioApellido": "García",
    "usuarioEmail": "ana_dup_nit@test.com",
    "usuarioPassword": "Abc12345",
}


class TestNitDuplicado:
    """POST /api/organizaciones/autorregistro — rechazo de NIT ya registrado."""

    def test_primer_registro_exitoso(self, client):
        """El primer registro con un NIT nuevo debe devolver 200."""
        res = client.post("/api/organizaciones/autorregistro", json=PAYLOAD_BASE)
        assert res.status_code == 200

    def test_segundo_registro_mismo_nit_409(self, client):
        """Un segundo registro con el mismo NIT debe devolver 409 con mensaje exacto."""
        # Asegurar que la organización ya exista (primer registro)
        client.post("/api/organizaciones/autorregistro", json=PAYLOAD_BASE)

        # Segundo intento con el mismo NIT (email diferente para no chocar por email)
        payload_dup = {**PAYLOAD_BASE, "usuarioEmail": "ana_dup_nit2@test.com"}
        res = client.post("/api/organizaciones/autorregistro", json=payload_dup)
        assert res.status_code == 409
        data = res.json()
        assert data.get("error") == "Ya existe una organización registrada con este NIT."
