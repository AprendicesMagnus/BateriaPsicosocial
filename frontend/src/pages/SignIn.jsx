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
      const data = await login({
        email,
        password
      });

      iniciarSesion(
        data.token,
        data.usuario
      );

      navigate("/panel");

    } catch (err) {

      if (err.payload?.requiresVerification) {

        navigate("/verificar-cuenta", {
          state: {
            email: err.payload.email
          }
        });

        return;
      }

      setError(
        err.message || "No se pudo iniciar sesión."
      );

    } finally {

      setLoading(false);

    }
  }

  return (
    <AuthLayout>

      <div className="login-container">

        {/* =================================================
            LOGO DE MAGNUS SIG

            El archivo está ubicado en:

            public/logo oscu.png

            Por eso se utiliza:
            /logo oscu.png
            ================================================= */}

        <img
          src="/logo oscu.png"
          alt="Magnus SIG"
          className="login-logo"
        />

        {/* =================================================
            TÍTULO
            ================================================= */}

        <h1>
          Inicio de Sesión
        </h1>

        {/* =================================================
            MENSAJE DE ÉXITO
            ================================================= */}

        <FormMessage type="success">
          {successMessage}
        </FormMessage>

        {/* =================================================
            MENSAJE DE ERROR
            ================================================= */}

        <FormMessage type="error">
          {error}
        </FormMessage>

        {/* =================================================
            FORMULARIO
            ================================================= */}

        <form
          className="auth-form"
          onSubmit={handleSubmit}
        >

          {/* CORREO */}

          <TextField
            label="Correo"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Correo"
          />

          {/* CONTRASEÑA */}

          <PasswordField
            label="Contraseña"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Contraseña"
          />

          {/* =================================================
              ENLACES
              ================================================= */}

          <div className="auth-links">

            <span>
              ¿No tienes cuenta?{" "}

              <Link
                className="link-accent"
                to="/crear-cuenta"
              >
                Crea una cuenta
              </Link>
            </span>

            <Link
              className="link-accent"
              to="/olvide-contrasena"
            >
              ¿Olvidaste tu contraseña?
            </Link>

          </div>

          {/* =================================================
              BOTÓN INICIAR SESIÓN
              ================================================= */}

          <PrimaryButton
            type="submit"
            loading={loading}
          >
            Iniciar Sesión
          </PrimaryButton>

          {/* =================================================
              SEPARADOR
              ================================================= */}

          <div className="divider">
            <span>o</span>
          </div>

          {/* =================================================
              GOOGLE
              ================================================= */}

          <SecondaryButton
            disabled
            title="Disponible próximamente"
          >
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