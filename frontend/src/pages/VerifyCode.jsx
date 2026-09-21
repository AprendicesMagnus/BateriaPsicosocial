import { useEffect, useState } from "react";
import { useLocation, useNavigate, Link } from "react-router-dom";
import { CodeInput, PrimaryButton, FormMessage } from "../components/FormControls";
import { verifyEmail, verifyResetCode, resendCode } from "../api/auth";
import "../styles/auth.css";
import { soloDigitos } from "../utils/validaciones";

const RESEND_SECONDS = 45;

function VerifyCodeBackground() {
  return <img src="/imagen5.jpg" alt="" className="verify-bg" />;
}

export default function VerifyCode({ mode }) {
  const location = useLocation();
  const navigate = useNavigate();
  const email = location.state?.email;

  const [codigo, setCodigo] = useState("");
  const [tocados, setTocados] = useState({});
  const [intento, setIntento] = useState(false);

  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [loading, setLoading] = useState(false);
  const [cooldown, setCooldown] = useState(0);

  const esReset = mode === "reset";

  useEffect(() => {
    if (!email) {
      navigate(esReset ? "/olvide-contrasena" : "/crear-cuenta", { replace: true });
    }
  }, [email, esReset, navigate]);

  useEffect(() => {
    if (cooldown <= 0) return;
    const timer = setInterval(() => setCooldown((c) => c - 1), 1000);
    return () => clearInterval(timer);
  }, [cooldown]);

  const marcar = (campo) => {
    setTocados((prev) => ({ ...prev, [campo]: true }));
  };

  const errores = {
    codigo: !codigo
      ? "Este campo es obligatorio."
      : !/^\d{6}$/.test(codigo.trim())
      ? "El código debe tener exactamente 6 dígitos."
      : "",
  };

  const mostrarError = (campo) => Boolean((tocados[campo] || intento) && errores[campo]);

  async function handleSubmit(e) {
    if (e) e.preventDefault();
    setError("");
    setInfo("");
    setIntento(true);

    if (errores.codigo) {
      setTimeout(() => {
        document.querySelector(".field__input--invalid")?.focus();
      }, 0);
      return;
    }

    const codTrim = codigo.trim();
    setLoading(true);
    try {
      if (esReset) {
        const data = await verifyResetCode({ email, codigo: codTrim });
        navigate("/restablecer-contrasena", { state: { email, resetToken: data.resetToken } });
      } else {
        await verifyEmail({ email, codigo: codTrim });
        navigate("/iniciar-sesion", {
          state: { message: "Cuenta verificada correctamente. Ya puedes iniciar sesión." },
        });
      }
    } catch (err) {
      setError(err.message || "Código inválido o expirado.");
    } finally {
      setLoading(false);
    }
  }

  async function handleResend() {
    setError("");
    setInfo("");
    try {
      await resendCode({
        email,
        tipo: esReset ? "RESET_PASSWORD" : "VERIFICACION_EMAIL",
      });
      setInfo("Hemos enviado un nuevo código a tu correo.");
      setCooldown(RESEND_SECONDS);
    } catch (err) {
      setError(err.message);
    }
  }

  if (!email) return null;

  return (
    <div className="verify-shell">
      <VerifyCodeBackground />

      <div className="verify-card">
        <img src="/logo oscu.png" alt="Magnus SIG" className="login-logo" />

        <h1>{esReset ? "Verificar Código" : "Verifica tu Correo"}</h1>

        <p className="auth-subtitle">
          Ingresa el código de 6 dígitos que enviamos a{" "}
          <span className="verification-email">{email}</span>
        </p>

        <FormMessage type="error">{error}</FormMessage>
        <FormMessage type="success">{info}</FormMessage>

        <form className="auth-form" onSubmit={handleSubmit} noValidate>
          <div className="field">
            <span className="field__label">Código de Verificación</span>
            <CodeInput
              value={codigo}
              onChange={(val) => setCodigo(soloDigitos(val, 6))}
              onBlur={() => marcar("codigo")}
              error={mostrarError("codigo") ? errores.codigo : ""}
            />
          </div>

          <PrimaryButton type="submit" loading={loading}>
            {esReset ? "Restablecer Contraseña" : "Verificar mi cuenta"}
          </PrimaryButton>

          <div className="resend-row">
            ¿No recibiste el código?{" "}
            {cooldown > 0 ? (
              <span>Reenviar en {cooldown}s</span>
            ) : (
              <button
                type="button"
                className="link-accent"
                onClick={handleResend}
                style={{ background: "none", border: "none" }}
              >
                Reenviar
              </button>
            )}
          </div>

          <Link className="back-link" to="/iniciar-sesion">
            ← Volver a inicio de sesión
          </Link>
        </form>
      </div>
    </div>
  );
}