import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import AuthLayout from "../components/AuthLayout";
import { TextField, PasswordField, PrimaryButton, SecondaryButton, FormMessage } from "../components/FormControls";
import { register } from "../api/auth";

const PASSWORD_HINT =
  "Mínimo 8 caracteres, con mayúsculas, minúsculas y números.";

export default function CreateAccount() {
  const [form, setForm] = useState({
    nombre: "",
    apellido: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  function update(field) {
    return (e) => setForm((f) => ({ ...f, [field]: e.target.value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");

    if (form.password !== form.confirmPassword) {
      setError("Las contraseñas no coinciden.");
      return;
    }

    setLoading(true);
    try {
      await register({
        nombre: form.nombre,
        apellido: form.apellido,
        email: form.email,
        password: form.password,
      });
      navigate("/verificar-cuenta", { state: { email: form.email } });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout illustration="network">
      <img src="/logo oscu.png" alt="Magnus SIG" className="login-logo" />
      <h1 style={{ textAlign: "center" }}>Crear Cuenta</h1>

      <FormMessage type="error">{error}</FormMessage>

      <form className="auth-form" onSubmit={handleSubmit}>
        <div className="form-row">
          <TextField
            label="Nombre"
            required
            value={form.nombre}
            onChange={update("nombre")}
            placeholder="Nombre"
          />
          <TextField
            label="Apellido"
            required
            value={form.apellido}
            onChange={update("apellido")}
            placeholder="Apellido"
          />
        </div>

        <TextField
          label="Correo electrónico"
          type="email"
          required
          value={form.email}
          onChange={update("email")}
          placeholder="nombre@empresa.com"
        />
        <PasswordField
          label="Contraseña"
          required
          minLength={8}
          value={form.password}
          onChange={update("password")}
          placeholder="••••••••"
        />
        <p className="auth-subtitle" style={{ margin: "-8px 0 0", fontSize: 12 }}>
          {PASSWORD_HINT}
        </p>
        <PasswordField
          label="Confirmar contraseña"
          required
          value={form.confirmPassword}
          onChange={update("confirmPassword")}
          placeholder="••••••••"
        />

        <div className="auth-links">
          <span>
            ¿Ya tienes cuenta?{" "}
            <Link className="link-accent" to="/iniciar-sesion">
              Inicia sesión
            </Link>
          </span>
        </div>

        <PrimaryButton type="submit" loading={loading}>
          Crear Cuenta
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
    </AuthLayout>
  );
}
