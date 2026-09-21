import { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";

import AuthLayout from "../components/AuthLayout";
import {
  TextField,
  PasswordField,
  PrimaryButton,
  SecondaryButton,
  FormMessage
} from "../components/FormControls";

import { login } from "../api/auth";
import { useAuth } from "../context/AuthContext";
import { emailValido, normalizarEmail } from "../utils/validaciones";

export default function SignIn() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [tocados, setTocados] = useState({});
  const [intento, setIntento] = useState(false);

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const { iniciarSesion } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const successMessage = location.state?.message;

  const marcar = (campo) => {
    setTocados((prev) => ({ ...prev, [campo]: true }));
  };

  const errores = {
    email: !email
      ? "Este campo es obligatorio."
      : !emailValido(normalizarEmail(email))
      ? "Ingresa un correo válido."
      : "",
    password: !password ? "Este campo es obligatorio." : "",
  };

  const mostrarError = (campo) => Boolean((tocados[campo] || intento) && errores[campo]);

  async function handleSubmit(e) {
    if (e) e.preventDefault();
    setError("");
    setIntento(true);

    const hayErrores = Object.keys(errores).some((campo) => Boolean(errores[campo]));
    if (hayErrores) {
      setTimeout(() => {
        document.querySelector(".field__input--invalid")?.focus();
      }, 0);
      return;
    }

    const correoNorm = normalizarEmail(email);
    setLoading(true);

    try {
      const data = await login({
        email: correoNorm,
        password
      });

      iniciarSesion(data.token, data.usuario);
      navigate("/panel");
    } catch (err) {
      if (err.payload?.requiresVerification) {
        navigate("/verificar-cuenta", {
          state: { email: err.payload.email }
        });
        return;
      }
      setError(err.message || "No se pudo iniciar sesión.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout>
      <div className="login-container">
        <img
          src="/logo oscu.png"
          alt="Magnus SIG"
          className="login-logo"
        />

        <h1>Inicio de Sesión</h1>

        <FormMessage type="success">{successMessage}</FormMessage>
        <FormMessage type="error">{error}</FormMessage>

        <form className="auth-form" onSubmit={handleSubmit} noValidate>
          <TextField
            label="Correo"
            type="email"
            maxLength={180}
            value={email}
            onChange={(e) => setEmail(normalizarEmail(e.target.value))}
            onBlur={() => marcar("email")}
            error={mostrarError("email") ? errores.email : ""}
            placeholder="Correo"
          />

          <PasswordField
            label="Contraseña"
            maxLength={72}
            value={password}
            onChange={(e) => setPassword(e.target.value.slice(0, 72))}
            onBlur={() => marcar("password")}
            error={mostrarError("password") ? errores.password : ""}
            placeholder="Contraseña"
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

          <div className="divider">
            <span>o</span>
          </div>

          <SecondaryButton disabled title="Disponible próximamente">
            <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true">
              <path fill="#4285F4" d="M17.64 9.2c0-.64-.06-1.25-.16-1.84H9v3.48h4.84a4.14 4.14 0 0 1-1.8 2.72v2.26h2.9c1.7-1.57 2.7-3.87 2.7-6.62z" />
              <path fill="#34A853" d="M9 18c2.43 0 4.47-.81 5.96-2.18l-2.9-2.26c-.81.54-1.84.86-3.06.86-2.35 0-4.34-1.59-5.05-3.72H.96v2.33A9 9 0 0 0 9 18z" />
              <path fill="#FBBC05" d="M3.95 10.7A5.4 5.4 0 0 1 3.67 9c0-.59.1-1.17.28-1.7V4.97H.96A9 9 0 0 0 0 9c0 1.45.35 2.83.96 4.03l2.99-2.33z" />
              <path fill="#EA4335" d="M9 3.58c1.32 0 2.51.46 3.44 1.35l2.58-2.58C13.46.89 11.43 0 9 0A9 9 0 0 0 .96 4.97l2.99 2.33C4.66 5.17 6.65 3.58 9 3.58z" />
            </svg>
            Continuar con Google
          </SecondaryButton>
        </form>
      </div>
    </AuthLayout>
  );
}