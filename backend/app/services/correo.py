import logging
import smtplib
import ssl
from email.message import EmailMessage

from app.core.config import get_settings

logger = logging.getLogger("magnussig.correo")

SMTP_TIMEOUT = 20  # segundos


def _abrir_conexion(host: str, port: int) -> smtplib.SMTP:
    """Abre la conexión SMTP según el puerto.

    - 465: TLS implícito (SMTP_SSL) con contexto SSL seguro. Es la opción recomendada para Gmail.
    - Otros (587, 25...): conexión normal + STARTTLS con el mismo contexto seguro.
    """
    contexto = ssl.create_default_context()

    if port == 465:
        return smtplib.SMTP_SSL(host, port, timeout=SMTP_TIMEOUT, context=contexto)

    servidor = smtplib.SMTP(host, port, timeout=SMTP_TIMEOUT)
    servidor.ehlo()
    servidor.starttls(context=contexto)
    servidor.ehlo()
    return servidor


def enviar_correo(destino: str, asunto: str, contenido: str) -> bool:
    settings = get_settings()
    if not settings.smtp_host:
        logger.info("Correo simulado para %s | asunto=%s | contenido=%s", destino, asunto, contenido)
        return True

    remitente = settings.smtp_from or settings.smtp_user or "noreply@magnussig.com"

    mensaje = EmailMessage()
    mensaje["From"] = remitente
    mensaje["To"] = destino
    mensaje["Subject"] = asunto
    mensaje.set_content(contenido)

    # Las contraseñas de aplicación de Gmail se muestran con espacios ("abcd efgh ijkl mnop");
    # SMTP necesita los 16 caracteres seguidos.
    password = (settings.smtp_pass or "").replace(" ", "")

    # Se intenta primero el puerto configurado y, si el servidor corta la conexión,
    # el puerto alterno de Gmail (465 <-> 587), por si uno está bloqueado en tu red/antivirus.
    puertos = [settings.smtp_port]
    alterno = 587 if settings.smtp_port == 465 else 465
    if settings.smtp_host.endswith("gmail.com"):
        puertos.append(alterno)

    ultimo_error: Exception | None = None
    for puerto in puertos:
        try:
            with _abrir_conexion(settings.smtp_host, puerto) as server:
                if settings.smtp_user:
                    server.login(settings.smtp_user, password)
                server.send_message(mensaje)
            logger.info("Correo enviado a %s por %s:%s", destino, settings.smtp_host, puerto)
            return True
        except smtplib.SMTPAuthenticationError as err:
            logger.error(
                "Autenticación SMTP rechazada para %s (revisa SMTP_USER y que SMTP_PASS sea una "
                "contraseña de aplicación de Gmail) | error=%s",
                settings.smtp_user,
                err,
            )
            return False
        except Exception as err:
            ultimo_error = err
            logger.warning(
                "SMTP %s:%s falló (%s: %s)", settings.smtp_host, puerto, type(err).__name__, err
            )

    logger.error("Falló el envío de correo SMTP a %s | error=%s", destino, ultimo_error)
    return False


def enviar_codigo_verificacion(destino: str, nombre: str, codigo: str, tipo: str) -> bool:
    asunto = (
        "Magnus|SIG - Código para restablecer tu contraseña"
        if tipo == "RESET_PASSWORD"
        else "Magnus|SIG - Verifica tu cuenta"
    )
    if tipo == "RESET_PASSWORD":
        texto = (
            f"Hola {nombre}, tu código para restablecer la contraseña es: {codigo}. "
            "Vence en 15 minutos."
        )
    else:
        texto = (
            f"Hola {nombre}, tu código de verificación de cuenta es: {codigo}. "
            "Vence en 15 minutos."
        )
    return enviar_correo(destino, asunto, texto)