import { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import AuthLayout from "../components/AuthLayout";
import { TextField, PasswordField, PrimaryButton, SecondaryButton, FormMessage } from "../components/FormControls";
import { login } from "../api/auth";
import { useAuth } from "../context/AuthContext";

export default function SignIn() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { iniciarSesion } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const successMessage = location.state?.message;

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await login({ email, password });
      iniciarSesion(data.token, data.usuario);
      navigate("/panel");
    } catch (err) {
      if (err.payload?.requiresVerification) {
        navigate("/verificar-cuenta", { state: { email: err.payload.email } });
        return;
      }
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout illustration="network">
      <h1>Inicio de Sesión</h1>
      <p className="auth-subtitle">
        Ingresa a tu cuenta para aplicar o consultar la Batería de Riesgo Psicosocial.
      </p>

      <FormMessage type="success">{successMessage}</FormMessage>
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
        <PasswordField
          label="Contraseña"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="••••••••"
        />

        <div className="auth-links">
          <span>
            ¿No tienes cuenta?{" "}
            <Link className="link-accent" to="/crear-cuenta">
              Crea una cuenta
            </Link>
          </span>
          <Link className="link-accent" to="/olvide-contrasena">
            ¿Olvidaste tu contraseña?
          </Link>
        </div>

        <PrimaryButton type="submit" loading={loading}>
          Iniciar Sesión
        </PrimaryButton>

        <div className="divider">o</div>

        <SecondaryButton disabled title="Disponible próximamente">
          Continuar con Google
        </SecondaryButton>
      </form>
    </AuthLayout>
  );
}
