"""Diagnostico de la conexion SMTP configurada en el .env.

Uso, desde la carpeta backend con el entorno virtual activo:
    python scripts/probar_smtp.py
    python scripts/probar_smtp.py --enviar destino@correo.com

Sin --enviar no se envia ningun correo: solo se comprueba la red, el cifrado y el login.
"""
import argparse
import smtplib
import socket
import ssl
import sys
from email.message import EmailMessage
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings  # noqa: E402

TIMEOUT = 15


def _paso(descripcion, funcion):
    try:
        resultado = funcion()
    except smtplib.SMTPResponseException as err:
        try:
            texto_error = err.smtp_error.decode("utf-8", errors="replace") if isinstance(err.smtp_error, bytes) else str(err.smtp_error)
        except Exception:
            texto_error = str(err.smtp_error)
        print(f"  [FALLO] {descripcion}: {type(err).__name__}: {err.smtp_code} {texto_error}")
        return None, False
    except Exception as err:
        print(f"  [FALLO] {descripcion}: {type(err).__name__}: {err}")
        return None, False
    print(f"  [OK]    {descripcion}")
    return resultado, True


def _emisor_certificado(servidor) -> str:
    try:
        certificado = servidor.sock.getpeercert()
        emisor = dict(campo[0] for campo in certificado.get("issuer", ()))
        return emisor.get("organizationName") or emisor.get("commonName") or "desconocido"
    except Exception:
        return "no disponible"


def _mensaje(remitente: str, destino: str) -> EmailMessage:
    mensaje = EmailMessage()
    mensaje["From"] = remitente
    mensaje["To"] = destino
    mensaje["Subject"] = "Magnus|SIG - Prueba de conexion SMTP"
    mensaje.set_content("Correo de prueba generado por scripts/probar_smtp.py.")
    return mensaje


def revisar_credenciales(usuario: str, password_bruta: str) -> None:
    password = password_bruta.replace(" ", "")
    con_comillas = password_bruta[:1] in ("'", '"') or password_bruta[-1:] in ("'", '"')
    formato_tipico = len(password) == 16 and password.isascii() and password.isalpha() and password.islower()
    print("Revision de credenciales (no se muestra la contrasena)")
    print(f"  Longitud original: {len(password_bruta)} | sin espacios: {len(password)}")
    print(f"  Comillas en los extremos: {con_comillas}")
    print(f"  Formato tipico de contrasena de aplicacion (16 letras minusculas): {formato_tipico}")
    print(f"  Usuario con formato de correo y sin espacios: {'@' in usuario and ' ' not in usuario}")
    print()


def probar_mecanismos(host: str, usuario: str, password: str) -> None:
    print("Autenticacion por mecanismo (puerto 587)")
    for mecanismo in ("PLAIN", "LOGIN"):
        def intentar(mecanismo=mecanismo):
            servidor = smtplib.SMTP(host, 587, timeout=TIMEOUT)
            try:
                servidor.ehlo()
                servidor.starttls(context=ssl.create_default_context())
                servidor.ehlo()
                servidor.esmtp_features["auth"] = mecanismo
                return servidor.login(usuario, password)
            finally:
                try:
                    servidor.close()
                except Exception:
                    pass

        _paso(f"Login forzando {mecanismo}", intentar)
    print()


def probar_puerto(host, puerto, usuario, password, remitente, destino) -> bool:
    modo = "TLS implicito" if puerto == 465 else "STARTTLS"
    print(f"Puerto {puerto} ({modo})")

    _, ok = _paso("Conexion TCP", lambda: socket.create_connection((host, puerto), timeout=TIMEOUT).close())
    if not ok:
        return False

    contexto = ssl.create_default_context()

    def abrir():
        if puerto == 465:
            return smtplib.SMTP_SSL(host, puerto, timeout=TIMEOUT, context=contexto)
        servidor = smtplib.SMTP(host, puerto, timeout=TIMEOUT)
        servidor.ehlo()
        servidor.starttls(context=contexto)
        servidor.ehlo()
        return servidor

    servidor, ok = _paso("Negociacion SMTP y TLS", abrir)
    if not ok:
        return False

    try:
        print(f"  [INFO]  Certificado emitido por: {_emisor_certificado(servidor)}")
        print(f"  [INFO]  Mecanismos de login anunciados: {servidor.esmtp_features.get('auth', 'ninguno')}")
        _, ok = _paso("Autenticacion", lambda: servidor.login(usuario, password))
        if ok and destino:
            _, ok = _paso(
                f"Envio de prueba a {destino}",
                lambda: servidor.send_message(_mensaje(remitente, destino)),
            )
        return ok
    finally:
        try:
            servidor.quit()
        except Exception:
            pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnostico de SMTP")
    parser.add_argument("--enviar", metavar="DESTINO", help="Envia un correo de prueba a este destino")
    argumentos = parser.parse_args()

    configuracion = get_settings()
    if not configuracion.smtp_host:
        print("SMTP_HOST esta vacio en el .env: el sistema esta en modo de correo simulado.")
        return 1

    host = configuracion.smtp_host
    usuario = configuracion.smtp_user
    password_bruta = configuracion.smtp_pass or ""
    password = password_bruta.replace(" ", "")
    remitente = configuracion.smtp_from or usuario

    print(f"Servidor: {host} | usuario: {usuario or '(vacio)'} | puerto configurado: {configuracion.smtp_port}")
    try:
        direcciones = {info[4][0] for info in socket.getaddrinfo(host, None)}
        print(f"Resolucion DNS: {', '.join(sorted(direcciones))}")
    except OSError as err:
        print(f"Resolucion DNS fallida: {err}")
        return 1

    revisar_credenciales(usuario, password_bruta)

    resultados = {}
    for puerto in (587, 465):
        resultados[puerto] = probar_puerto(host, puerto, usuario, password, remitente, argumentos.enviar)
        print()

    if any(resultados.values()):
        print("Al menos un puerto funciona completo. Configura SMTP_PORT con ese puerto.")
        return 0

    probar_mecanismos(host, usuario, password)

    print("Ningun puerto funciono. Interpretacion segun el paso que fallo:")
    print("  - Conexion TCP: la red o el firewall bloquean la salida hacia ese puerto.")
    print("  - Negociacion SMTP y TLS: suele ser un antivirus o proxy que intercepta el cifrado de correo;")
    print("    revisa si el certificado lo emite una entidad distinta de Google.")
    print("  - Autenticacion: SMTP_USER o SMTP_PASS incorrectos; usa una contrasena de aplicacion de Gmail.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
