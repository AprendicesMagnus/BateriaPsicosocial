import { useEffect, useState } from "react";
import { useLocation, useNavigate, Link } from "react-router-dom";
import { CodeInput, PrimaryButton, FormMessage } from "../components/FormControls";
import { verifyEmail, verifyResetCode, resendCode } from "../api/auth";
import "../styles/auth.css";

const RESEND_SECONDS = 45;

// Imagen de fondo a toda pantalla (misma que Recuperar Contraseña).
// El archivo debe estar en: public/fondo-recuperar.jpg
function VerifyCodeBackground() {
  return <img src="/imagen5.jpg" alt="" className="verify-bg" />;
}

export default function VerifyCode({ mode }) {
  const location = useLocation();
  const navigate = useNavigate();
  const email = location.state?.email;

  const [codigo, setCodigo] = useState("");
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

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setInfo("");
    setLoading(true);
    try {
      if (esReset) {
        const data = await verifyResetCode({ email, codigo });
        navigate("/restablecer-contrasena", { state: { email, resetToken: data.resetToken } });
      } else {
        await verifyEmail({ email, codigo });
        navigate("/iniciar-sesion", {
          state: { message: "Cuenta verificada correctamente. Ya puedes iniciar sesión." },
        });
      }
    } catch (err) {
      setError(err.message);
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

        {/* =================================================
            TÍTULO
            Cambia según el uso de la pantalla:
            - reset  -> viene de "Olvidé mi contraseña"
            - normal -> viene de "Crear cuenta"
            ================================================= */}
        <h1>{esReset ? "Verificar Código" : "Verifica tu Correo"}</h1>

        <p className="auth-subtitle">
          Ingresa el código de 6 dígitos que enviamos a{" "}
          <span className="verification-email">{email}</span>
        </p>

        <FormMessage type="error">{error}</FormMessage>
        <FormMessage type="success">{info}</FormMessage>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label className="field">
            <span className="field__label">Código de Verificación</span>
            <CodeInput value={codigo} onChange={setCodigo} />
          </label>

          <PrimaryButton type="submit" loading={loading} disabled={codigo.length !== 6}>
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