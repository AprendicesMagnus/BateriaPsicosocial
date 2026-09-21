import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import AuthLayout from "../components/AuthLayout";
import { TextField, PasswordField, PrimaryButton, SecondaryButton, FormMessage } from "../components/FormControls";
import { register } from "../api/auth";
import {
  TEXTO_AYUDA_PASSWORD,
  emailValido,
  filtrarNombrePersona,
  nombrePersonaValido,
  normalizarEmail,
  passwordValida,
} from "../utils/validaciones";

export default function CreateAccount() {
  const [form, setForm] = useState({
    nombre: "",
    apellido: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [tocados, setTocados] = useState({});
  const [intento, setIntento] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const marcar = (campo) => {
    setTocados((prev) => ({ ...prev, [campo]: true }));
  };

  const errores = {
    nombre: !form.nombre
      ? "Este campo es obligatorio."
      : !nombrePersonaValido(form.nombre.trim(), 100)
      ? "Solo letras y espacios (mínimo 2 caracteres)."
      : "",
    apellido: !form.apellido
      ? "Este campo es obligatorio."
      : !nombrePersonaValido(form.apellido.trim(), 100)
      ? "Solo letras y espacios (mínimo 2 caracteres)."
      : "",
    email: !form.email
      ? "Este campo es obligatorio."
      : !emailValido(normalizarEmail(form.email))
      ? "Ingresa un correo válido."
      : "",
    password: !form.password
      ? "Este campo es obligatorio."
      : !passwordValida(form.password)
      ? TEXTO_AYUDA_PASSWORD
      : "",
    confirmPassword: !form.confirmPassword
      ? "Este campo es obligatorio."
      : form.password !== form.confirmPassword
      ? "Las contraseñas no coinciden."
      : "",
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

    const nomTrim = form.nombre.trim();
    const apeTrim = form.apellido.trim();
    const correoNorm = normalizarEmail(form.email);

    setLoading(true);
    try {
      await register({
        nombre: nomTrim,
        apellido: apeTrim,
        email: correoNorm,
        password: form.password,
      });
      navigate("/verificar-cuenta", { state: { email: correoNorm } });
    } catch (err) {
      setError(err.message || "No se pudo crear la cuenta.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout illustration="network">
      <img src="/logo oscu.png" alt="Magnus SIG" className="login-logo" />
      <h1 style={{ textAlign: "center" }}>Crear Cuenta</h1>

      <FormMessage type="error">{error}</FormMessage>

      <form className="auth-form" onSubmit={handleSubmit} noValidate>
        <div className="form-row">
          <TextField
            label="Nombre"
            maxLength={100}
            value={form.nombre}
            onChange={(e) => setForm((f) => ({ ...f, nombre: filtrarNombrePersona(e.target.value, 100) }))}
            onBlur={() => marcar("nombre")}
            error={mostrarError("nombre") ? errores.nombre : ""}
            placeholder="Nombre"
          />
          <TextField
            label="Apellido"
            maxLength={100}
            value={form.apellido}
            onChange={(e) => setForm((f) => ({ ...f, apellido: filtrarNombrePersona(e.target.value, 100) }))}
            onBlur={() => marcar("apellido")}
            error={mostrarError("apellido") ? errores.apellido : ""}
            placeholder="Apellido"
          />
        </div>

        <TextField
          label="Correo electrónico"
          type="email"
          maxLength={180}
          value={form.email}
          onChange={(e) => setForm((f) => ({ ...f, email: normalizarEmail(e.target.value) }))}
          onBlur={() => marcar("email")}
          error={mostrarError("email") ? errores.email : ""}
          placeholder="nombre@empresa.com"
        />

        <PasswordField
          label="Contraseña"
          maxLength={72}
          value={form.password}
          onChange={(e) => setForm((f) => ({ ...f, password: e.target.value.slice(0, 72) }))}
          onBlur={() => marcar("password")}
          error={mostrarError("password") ? errores.password : ""}
          placeholder="••••••••"
        />

        <PasswordField
          label="Confirmar contraseña"
          maxLength={72}
          value={form.confirmPassword}
          onChange={(e) => setForm((f) => ({ ...f, confirmPassword: e.target.value.slice(0, 72) }))}
          onBlur={() => marcar("confirmPassword")}
          error={mostrarError("confirmPassword") ? errores.confirmPassword : ""}
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
