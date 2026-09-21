import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { TextField, PrimaryButton, FormMessage } from "../components/FormControls";
import { forgotPassword } from "../api/auth";
import "../styles/auth.css";
import { emailValido, normalizarEmail } from "../utils/validaciones";

function ForgotPasswordBackground() {
  return <img src="/imagen5.jpg" alt="" className="verify-bg" />;
}

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [tocados, setTocados] = useState({});
  const [intento, setIntento] = useState(false);

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const marcar = (campo) => {
    setTocados((prev) => ({ ...prev, [campo]: true }));
  };

  const errores = {
    email: !email
      ? "Este campo es obligatorio."
      : !emailValido(normalizarEmail(email))
      ? "Ingresa un correo válido."
      : "",
  };

  const mostrarError = (campo) => Boolean((tocados[campo] || intento) && errores[campo]);

  async function handleSubmit(e) {
    if (e) e.preventDefault();
    setError("");
    setIntento(true);

    if (errores.email) {
      setTimeout(() => {
        document.querySelector(".field__input--invalid")?.focus();
      }, 0);
      return;
    }

    const correoNorm = normalizarEmail(email);
    setLoading(true);
    try {
      await forgotPassword({ email: correoNorm });
      navigate("/verificar-codigo", { state: { email: correoNorm } });
    } catch (err) {
      setError(err.message || "No se pudo enviar el código de recuperación.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="verify-shell">
      <ForgotPasswordBackground />

      <div className="verify-card">
        <img src="/logo oscu.png" alt="Magnus SIG" className="login-logo" />

        <h1>Recuperar Contraseña</h1>
        <p className="auth-subtitle">
          Ingresa el correo asociado a tu cuenta y te enviaremos un código para restablecer tu contraseña.
        </p>

        <FormMessage type="error">{error}</FormMessage>

        <form className="auth-form" onSubmit={handleSubmit} noValidate>
          <TextField
            label="Correo electrónico"
            type="email"
            maxLength={180}
            value={email}
            onChange={(e) => setEmail(normalizarEmail(e.target.value))}
            onBlur={() => marcar("email")}
            error={mostrarError("email") ? errores.email : ""}
            placeholder="nombre@empresa.com"
          />

          <PrimaryButton type="submit" loading={loading}>
            Enviar Código
          </PrimaryButton>

          <Link className="back-link" to="/iniciar-sesion">
            ← Volver a inicio de sesión
          </Link>
        </form>
      </div>
    </div>
  );
}