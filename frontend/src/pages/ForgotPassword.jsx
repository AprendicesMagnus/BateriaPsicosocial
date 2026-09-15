import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { TextField, PrimaryButton, FormMessage } from "../components/FormControls";
import { forgotPassword } from "../api/auth";
import "../styles/auth.css";

// Ilustración de fondo decorativa: dos personas conversando en un sofá,
// con un reloj y un globo de chat grandes de fondo (placeholder mientras
// se consigue la imagen definitiva).
function ForgotPasswordBackground() {
  return (
    <img src="/imagen5.jpg" alt="" className="verify-bg" />
  );
}

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await forgotPassword({ email });
      navigate("/verificar-codigo", { state: { email } });
    } catch (err) {
      setError(err.message);
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

        <form className="auth-form" onSubmit={handleSubmit}>
          <TextField
            label="Correo electrónico"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
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