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
      <h1>Crear Cuenta</h1>
      <p className="auth-subtitle">
        Regístrate como evaluador SST, administrador o trabajador para acceder a la plataforma.
      </p>

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

        <div className="divider">o</div>

        <SecondaryButton disabled title="Disponible próximamente">
          Continuar con Google
        </SecondaryButton>
      </form>
    </AuthLayout>
  );
}
