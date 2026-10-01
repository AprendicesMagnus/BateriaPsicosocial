"""Muestra la conversación SMTP completa. Ejecutar desde backend/:  python probar_smtp_debug.py"""
import base64
import smtplib
import ssl

from app.core.config import get_settings

s = get_settings()
pass_ = (s.smtp_pass or "").replace(" ", "")
ctx = ssl.create_default_context()


def conectar():
    srv = smtplib.SMTP_SSL(s.smtp_host, 465, timeout=20, context=ctx)
    srv.set_debuglevel(1)
    code, msg = srv.ehlo()
    print(f">>> EHLO respondió {code}")
    return srv


print("\n##### PRUEBA A: AUTH PLAIN manual #####")
try:
    srv = conectar()
    token = base64.b64encode(f"\0{s.smtp_user}\0{pass_}".encode()).decode()
    print(">>> Respuesta:", srv.docmd("AUTH", "PLAIN " + token))
except Exception as e:
    print(f">>> FALLÓ: {type(e).__name__}: {e}")

print("\n##### PRUEBA B: AUTH LOGIN manual #####")
try:
    srv = conectar()
    print(">>> Respuesta 1:", srv.docmd("AUTH", "LOGIN"))
    print(">>> Respuesta 2:", srv.docmd(base64.b64encode(s.smtp_user.encode()).decode()))
    print(">>> Respuesta 3:", srv.docmd(base64.b64encode(pass_.encode()).decode()))
except Exception as e:
    print(f">>> FALLÓ: {type(e).__name__}: {e}")