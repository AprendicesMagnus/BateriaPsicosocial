"""Diagnóstico SMTP. Ejecutar desde la carpeta backend:  python probar_smtp.py
Prueba cada paso por separado para ver exactamente dónde se corta la conexión."""
import smtplib
import socket
import ssl

from app.core.config import get_settings

s = get_settings()
print(f"Config leída -> host={s.smtp_host!r} puerto={s.smtp_port} user={s.smtp_user!r} "
      f"pass_len={len((s.smtp_pass or '').replace(' ', ''))} (debe ser 16 en Gmail)")
if not s.smtp_host:
    raise SystemExit("SMTP_HOST está vacío: el .env no se está leyendo (ejecuta desde backend/).")

pass_ = (s.smtp_pass or "").replace(" ", "")
ctx = ssl.create_default_context()

for puerto in (465, 587):
    print(f"\n=== Puerto {puerto} ===")
    try:
        sock = socket.create_connection((s.smtp_host, puerto), timeout=15)
        print("1) TCP conectado OK")
        sock.close()
    except Exception as e:
        print(f"1) TCP FALLÓ: {type(e).__name__}: {e}  -> puerto bloqueado por firewall/red/ISP")
        continue
    try:
        if puerto == 465:
            srv = smtplib.SMTP_SSL(s.smtp_host, puerto, timeout=20, context=ctx)
        else:
            srv = smtplib.SMTP(s.smtp_host, puerto, timeout=20)
            srv.ehlo()
            srv.starttls(context=ctx)
            srv.ehlo()
        print("2) Handshake TLS OK")
    except Exception as e:
        print(f"2) TLS FALLÓ: {type(e).__name__}: {e}  -> antivirus/proxy/VPN interceptando SSL")
        continue
    try:
        srv.login(s.smtp_user, pass_)
        print("3) Login OK  -> credenciales correctas")
        srv.quit()
    except Exception as e:
        print(f"3) Login FALLÓ: {type(e).__name__}: {e}")