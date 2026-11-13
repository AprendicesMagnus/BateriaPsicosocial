import io
import uuid

PDF = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n"


def _admin(client):
    res = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['token']}"}


def _usuario_normal(client, headers_admin):
    from tests.test_soporte_mensajes import _crear_organizacion, _crear_usuario

    org = _crear_organizacion(client, headers_admin, "Org Docs " + uuid.uuid4().hex[:6])
    _, email = _crear_usuario(client, headers_admin, "EVALUADOR_SST", org, "Password1234")
    res = client.post("/api/auth/login", json={"email": email, "password": "Password1234"})
    return {"Authorization": f"Bearer {res.json()['token']}"}


def _subir(client, headers, nombre="Guia.pdf", contenido=PDF, titulo="Guía de prueba", activo="true"):
    return client.post(
        "/api/soporte/documentos",
        headers=headers,
        data={"titulo": titulo, "descripcion": "Descripción", "activo": activo},
        files={"archivo": (nombre, io.BytesIO(contenido), "application/octet-stream")},
    )


def test_admin_sube_y_usuario_descarga(client):
    admin = _admin(client)
    res = _subir(client, admin)
    assert res.status_code == 200, res.text
    doc = res.json()
    assert doc["extension"] == "pdf" and doc["tamano"] == len(PDF) and doc["activo"] is True

    normal = _usuario_normal(client, admin)
    lista = client.get("/api/soporte/documentos", headers=normal).json()
    assert any(d["id"] == doc["id"] for d in lista)
    assert "contenido" not in lista[0]

    r = client.get(f"/api/soporte/documentos/{doc['id']}/descargar", headers=normal)
    assert r.status_code == 200
    assert r.content == PDF
    assert r.headers["content-type"].startswith("application/pdf")
    assert r.headers["content-disposition"].startswith("attachment")
    assert r.headers["x-content-type-options"] == "nosniff"


def test_solo_admin_gestiona(client):
    admin = _admin(client)
    normal = _usuario_normal(client, admin)
    assert _subir(client, normal).status_code == 403
    assert client.get("/api/soporte/documentos/admin", headers=normal).status_code == 403
    doc = _subir(client, admin).json()
    assert client.patch(f"/api/soporte/documentos/{doc['id']}", headers=normal, json={"activo": False}).status_code == 403
    assert client.delete(f"/api/soporte/documentos/{doc['id']}", headers=normal).status_code == 403
    assert client.get("/api/soporte/documentos").status_code in (401, 403)


def test_validaciones_de_archivo(client):
    admin = _admin(client)
    r = _subir(client, admin, nombre="virus.exe", contenido=b"MZ....")
    assert r.status_code == 400 and "Formato no permitido" in r.json()["error"]
    r = _subir(client, admin, nombre="falso.pdf", contenido=b"<html><script>alert(1)</script>")
    assert r.status_code == 400 and "no es un .pdf válido" in r.json()["error"]
    r = _subir(client, admin, nombre="vacio.pdf", contenido=b"")
    assert r.status_code == 400
    r = _subir(client, admin, contenido=PDF + b"0" * (10 * 1024 * 1024))
    assert r.status_code == 400 and "10 MB" in r.json()["error"]
    r = _subir(client, admin, titulo="   ")
    assert r.status_code == 400
    # Word moderno (zip) sí se acepta
    r = _subir(client, admin, nombre="../../etc/Plantilla informe.docx", contenido=b"PK\x03\x04datos", titulo="Plantilla")
    assert r.status_code == 200 and r.json()["nombreArchivo"] == "Plantilla informe.docx"


def test_oculto_no_se_ve_ni_descarga_pero_admin_si(client):
    admin = _admin(client)
    normal = _usuario_normal(client, admin)
    doc = _subir(client, admin, activo="false").json()
    assert doc["activo"] is False
    assert all(d["id"] != doc["id"] for d in client.get("/api/soporte/documentos", headers=normal).json())
    assert client.get(f"/api/soporte/documentos/{doc['id']}/descargar", headers=normal).status_code == 404
    assert client.get(f"/api/soporte/documentos/{doc['id']}/descargar", headers=admin).status_code == 200
    # lo muestra y editar título
    r = client.patch(f"/api/soporte/documentos/{doc['id']}", headers=admin, json={"activo": True, "titulo": "Nuevo título"})
    assert r.status_code == 200 and r.json()["titulo"] == "Nuevo título"
    assert any(d["id"] == doc["id"] for d in client.get("/api/soporte/documentos", headers=normal).json())


def test_eliminar(client):
    admin = _admin(client)
    doc = _subir(client, admin).json()
    assert client.delete(f"/api/soporte/documentos/{doc['id']}", headers=admin).status_code == 200
    assert client.get(f"/api/soporte/documentos/{doc['id']}/descargar", headers=admin).status_code == 404
    assert client.delete(f"/api/soporte/documentos/{doc['id']}", headers=admin).status_code == 404
