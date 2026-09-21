import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { PasswordField, PrimaryButton, FormMessage } from "../components/FormControls";
import { resetPassword } from "../api/auth";
import "../styles/auth.css";
import { TEXTO_AYUDA_PASSWORD, passwordValida } from "../utils/validaciones";

function ResetPasswordBackground() {
  return <img src="/imagen5.jpg" alt="" className="verify-bg" />;
}

export default function ResetPassword() {
  const location = useLocation();
  const navigate = useNavigate();
  const { resetToken } = location.state || {};

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [tocados, setTocados] = useState({});
  const [intento, setIntento] = useState(false);

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!resetToken) {
      navigate("/olvide-contrasena", { replace: true });
    }
  }, [resetToken, navigate]);

  const marcar = (campo) => {
    setTocados((prev) => ({ ...prev, [campo]: true }));
  };

  const errores = {
    password: !password
      ? "Este campo es obligatorio."
      : !passwordValida(password)
      ? TEXTO_AYUDA_PASSWORD
      : "",
    confirmPassword: !confirmPassword
      ? "Este campo es obligatorio."
      : password !== confirmPassword
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

    setLoading(true);
    try {
      await resetPassword({ resetToken, password });
      navigate("/iniciar-sesion", {
        state: { message: "Contraseña restablecida con éxito. Ya puedes iniciar sesión." },
      });
    } catch (err) {
      setError(err.message || "No se pudo restablecer la contraseña.");
    } finally {
      setLoading(false);
    }
  }

  if (!resetToken) return null;

  return (
    <div className="verify-shell">
      <ResetPasswordBackground />

      <div className="verify-card">
        <img src="/logo oscu.png" alt="Magnus SIG" className="login-logo" />

        <h1>Restablecer Contraseña</h1>
        <p className="auth-subtitle">Crea una nueva contraseña segura para tu cuenta.</p>

        <FormMessage type="error">{error}</FormMessage>

        <form className="auth-form" onSubmit={handleSubmit} noValidate>
          <PasswordField
            label="Nueva Contraseña"
            maxLength={72}
            value={password}
            onChange={(e) => setPassword(e.target.value.slice(0, 72))}
            onBlur={() => marcar("password")}
            error={mostrarError("password") ? errores.password : ""}
            placeholder="••••••••"
          />

          <PasswordField
            label="Confirmar Contraseña"
            maxLength={72}
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value.slice(0, 72))}
            onBlur={() => marcar("confirmPassword")}
            error={mostrarError("confirmPassword") ? errores.confirmPassword : ""}
            placeholder="••••••••"
          />

          <PrimaryButton type="submit" loading={loading}>
            Confirmar Contraseña
          </PrimaryButton>
        </form>
      </div>
    </div>
  );
}