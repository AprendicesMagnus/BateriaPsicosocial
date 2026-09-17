import logging
import smtplib
from email.message import EmailMessage

from app.core.config import get_settings

logger = logging.getLogger("magnussig.correo")


def enviar_codigo_verificacion(destino: str, nombre: str, codigo: str, tipo: str) -> None:
    settings = get_settings()
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

    if not settings.smtp_host:
        logger.info("Correo simulado para %s | asunto=%s | codigo=%s", destino, asunto, codigo)
        return

    mensaje = EmailMessage()
    mensaje["From"] = settings.smtp_from
    mensaje["To"] = destino
    mensaje["Subject"] = asunto
    mensaje.set_content(texto)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls()
        if settings.smtp_user:
            server.login(settings.smtp_user, settings.smtp_pass)
        server.send_message(mensaje)
