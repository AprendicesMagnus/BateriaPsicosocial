"""
Tests de rechazo explícito (HTTP 422) y aceptación (HTTP 200/201) para el barrido sistemático de validaciones de Pydantic.

Verifica:
1. Nombre de persona con números, símbolos o '×' -> 422; 'María José', 'Núñez', '  Ana   María ' -> 200
2. Razón social '122' -> 422; 'Agro 2000 S.A.S.' -> 200
3. Municipio 'Neiva1' -> 422; 'Bogotá D.C.' -> 200
4. numeroTrabajadores 0 y 1000001 -> 422
5. Password < 8 caracteres o > 72 bytes -> 422
6. resend-code tipo VERIFICACION_EMAIL/RESET_PASSWORD -> 200; otro/verificacion_email -> 422
7. Número de tarjeta con espacios normalizado -> 200
8. Mensajes de error en español en respuesta 422 (propiedad 'error' traducida sin 'pattern' ni 'String should')
"""
import uuid


def test_rechazo_nombre_con_numeros(client):
    """Verifica que el schema de usuario rechace nombres con números."""
    res = client.post("/api/auth/register", json={
        "nombre": "Juan123",
        "apellido": "Pérez",
        "email": f"test_{uuid.uuid4().hex[:6]}@test.com",
        "password": "Password123"
    })
    assert res.status_code == 422


def test_rechazo_password_supera_72_caracteres(client):
    """Verifica que el schema rechace contraseñas de más de 72 caracteres (límite bcrypt)."""
    password_larga = "A1a!" + "x" * 70  # 74 caracteres
    res = client.post("/api/auth/register", json={
        "nombre": "Carlos",
        "apellido": "López",
        "email": f"test_{uuid.uuid4().hex[:6]}@test.com",
        "password": password_larga
    })
    assert res.status_code == 422


def test_rechazo_rol_codigo_minusculas(client):
    """Verifica que los códigos de rol deban ser en mayúsculas (r'^[A-Z0-9_]+$')."""
    res = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    assert res.status_code == 200
    headers = {"Authorization": f"Bearer {res.json()['token']}"}

    res_rol = client.post("/api/roles", headers=headers, json={
        "codigo": "rol_minuscula",
        "nombre": "Rol Inválido"
    })
    assert res_rol.status_code == 422


def test_rechazo_pago_cvv_invalido(client):
    """Verifica que un CVV con más de 4 dígitos sea rechazado por Pydantic."""
    res = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    assert res.status_code == 200
    headers = {"Authorization": f"Bearer {res.json()['token']}"}

    res_pago = client.post("/api/pagos", headers=headers, json={
        "compraId": str(uuid.uuid4()),
        "metodo": "tarjeta",
        "cvv": "12345"  # 5 dígitos, max 4
    })
    assert res_pago.status_code == 422


def test_nombre_persona_validations(client):
    """Prueba rechazos y aceptaciones de NombrePersona."""
    # Rechazos
    for nombre_invalido in ["Juan123", "Juan@#", "Juan×"]:
        res = client.post("/api/auth/register", json={
            "nombre": nombre_invalido,
            "apellido": "Pérez",
            "email": f"test_{uuid.uuid4().hex[:6]}@test.com",
            "password": "Password123"
        })
        assert res.status_code == 422, f"Debió rechazar {nombre_invalido}"

    # Aceptación con acentos, tildes, ñ y espacios múltiples que se normalizan
    res_ok = client.post("/api/auth/register", json={
        "nombre": "  Ana   María ",
        "apellido": "Núñez",
        "email": f"test_{uuid.uuid4().hex[:6]}@test.com",
        "password": "Password123"
    })
    assert res_ok.status_code == 200


def test_razon_social_validations(client):
    """Prueba rechazos y aceptaciones de RazonSocial en creación de organización."""
    res_login = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    headers = {"Authorization": f"Bearer {res_login.json()['token']}"}

    # Rechazo: "122" sin letras (RazonSocial exige al menos 2 letras)
    res_bad = client.post("/api/organizaciones", headers=headers, json={
        "nombre": "122",
        "nit": "899999068-1",
        "sector": "Tecnología",
        "direccion": "Calle 1",
        "municipio": "Bogotá",
        "departamento": "Cundinamarca"
    })
    assert res_bad.status_code == 422

    # Aceptación: "Agro 2000 S.A.S." con NIT válido (Bavaria 860005224-6)
    res_ok = client.post("/api/organizaciones", headers=headers, json={
        "nombre": "Agro 2000 S.A.S.",
        "nit": "860005224-6",
        "sector": "Tecnología",
        "direccion": "Calle 1",
        "municipio": "Bogotá",
        "departamento": "Cundinamarca"
    })
    assert res_ok.status_code in (200, 201)


def test_municipio_validations(client):
    """Prueba rechazos y aceptaciones de Municipio (Lugar)."""
    res_login = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    headers = {"Authorization": f"Bearer {res_login.json()['token']}"}

    # Rechazo: "Neiva1" con dígito
    res_bad = client.post("/api/organizaciones", headers=headers, json={
        "nombre": "Empresa Test 1",
        "nit": "860003020-1",
        "sector": "Servicios",
        "direccion": "Calle 2",
        "municipio": "Neiva1",
        "departamento": "Huila"
    })
    assert res_bad.status_code == 422

    # Aceptación: "Bogotá D.C." con NIT válido (DIAN 800197268-4)
    res_ok = client.post("/api/organizaciones", headers=headers, json={
        "nombre": "Empresa Test 2",
        "nit": "800197268-4",
        "sector": "Servicios",
        "direccion": "Calle 2",
        "municipio": "Bogotá D.C.",
        "departamento": "Cundinamarca"
    })
    assert res_ok.status_code in (200, 201)


def test_numero_trabajadores_validations(client):
    """Prueba que numeroTrabajadores fuera del rango [1, 1000000] sea rechazado."""
    res_login = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    headers = {"Authorization": f"Bearer {res_login.json()['token']}"}

    for num in [0, 1000001]:
        res = client.post("/api/organizaciones", headers=headers, json={
            "nombre": "Empresa Num Test",
            "nit": "899999001-7",
            "sector": "Servicios",
            "direccion": "Calle 2",
            "municipio": "Bogotá",
            "departamento": "Cundinamarca",
            "numeroTrabajadores": num
        })
        assert res.status_code == 422, f"Debió rechazar numeroTrabajadores={num}"


def test_password_validations(client):
    """Prueba rechazos de contraseña corta (<8) y contraseña larga por UTF-8 (>72 bytes)."""
    # Corta < 8 chars
    res_corta = client.post("/api/auth/register", json={
        "nombre": "Carlos",
        "apellido": "López",
        "email": f"test_{uuid.uuid4().hex[:6]}@test.com",
        "password": "Ab1!"
    })
    assert res_corta.status_code == 422

    # > 72 bytes en UTF-8 (ej. 20 emojis de 4 bytes cada uno + 4 chars = 84 bytes)
    password_multibyte = "😀" * 20 + "Aa1!"
    res_bytes = client.post("/api/auth/register", json={
        "nombre": "Carlos",
        "apellido": "López",
        "email": f"test_{uuid.uuid4().hex[:6]}@test.com",
        "password": password_multibyte
    })
    assert res_bytes.status_code == 422


def test_resend_code_tipo_validations(client):
    """Prueba que tipo en resend-code acepte VERIFICACION_EMAIL y RESET_PASSWORD y rechace otros."""
    # Aceptaciones
    res_1 = client.post("/api/auth/resend-code", json={
        "email": "admin@magnussig.com",
        "tipo": "VERIFICACION_EMAIL"
    })
    assert res_1.status_code == 200

    res_2 = client.post("/api/auth/resend-code", json={
        "email": "admin@magnussig.com",
        "tipo": "RESET_PASSWORD"
    })
    assert res_2.status_code == 200

    # Rechazos
    for tipo_inv in ["otro", "verificacion_email"]:
        res_bad = client.post("/api/auth/resend-code", json={
            "email": "admin@magnussig.com",
            "tipo": tipo_inv
        })
        assert res_bad.status_code == 422, f"Debió rechazar tipo={tipo_inv}"


def test_pago_numero_tarjeta_espacios(client):
    """Verifica que un número de tarjeta con espacios sea normalizado por el validator antes de procesar."""
    res_login = client.post("/api/auth/login", json={"email": "admin@magnussig.com", "password": "Admin1234"})
    headers = {"Authorization": f"Bearer {res_login.json()['token']}"}

    res_compra = client.post("/api/compras", headers=headers, json={
        "cantidad": 1,
        "bateriaNombre": "Batería Test"
    })
    assert res_compra.status_code in (200, 201)
    compra_id = res_compra.json()["id"]

    res_pago = client.post("/api/pagos", headers=headers, json={
        "compraId": compra_id,
        "metodo": "tarjeta",
        "numeroTarjeta": "4532 0151 1234 5678",  # Con espacios
        "nombreTarjeta": "JUAN PEREZ",
        "vencimiento": "12/28",
        "cvv": "123",
        "monto": 11900
    })
    assert res_pago.status_code == 200


def test_spanish_error_messages(client):
    """Verifica que las respuestas 422 devuelvan mensajes traducidos al español sin 'pattern' ni 'String should'."""
    res = client.post("/api/auth/register", json={
        "nombre": "Juan123",
        "apellido": "Pérez",
        "email": "email-invalido",
        "password": "123"
    })
    assert res.status_code == 422
    data = res.json()
    assert "error" in data
    mensaje_error = data["error"]
    assert "pattern" not in mensaje_error.lower()
    assert "string should" not in mensaje_error.lower()


def test_organizaciones_autorregistro_schema_validations(client):
    """Prueba rechazos 422 en POST /api/organizaciones/autorregistro para numeroTrabajadores, nombre y usuarioNombre."""
    payload_base = {
        "nit": "899999068-1",
        "nombre": "Empresa Válida S.A.S.",
        "sector": "Tecnología",
        "numeroTrabajadores": 50,
        "municipio": "Bogotá D.C.",
        "email": "empresa@test.com",
        "usuarioNombre": "Carlos",
        "usuarioApellido": "López",
        "usuarioEmail": f"user_{uuid.uuid4().hex[:6]}@test.com",
        "usuarioPassword": "Password123"
    }

    # numeroTrabajadores 0 y 1000001 devuelven 422
    for num in [0, 1000001]:
        bad_payload = dict(payload_base, numeroTrabajadores=num)
        res = client.post("/api/organizaciones/autorregistro", json=bad_payload)
        assert res.status_code == 422, f"Debió rechazar numeroTrabajadores={num}"

    # nombre "122" devuelve 422 (RazonSocial exige al menos 2 letras)
    bad_nombre = dict(payload_base, nombre="122")
    res_nom = client.post("/api/organizaciones/autorregistro", json=bad_nombre)
    assert res_nom.status_code == 422

    # usuarioNombre "1212122" devuelve 422 (NombrePersona sólo letras)
    bad_usr_nom = dict(payload_base, usuarioNombre="1212122")
    res_usr_nom = client.post("/api/organizaciones/autorregistro", json=bad_usr_nom)
    assert res_usr_nom.status_code == 422

