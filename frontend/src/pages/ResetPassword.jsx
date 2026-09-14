import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import AuthLayout from "../components/AuthLayout";
import { PasswordField, PrimaryButton, FormMessage } from "../components/FormControls";
import { resetPassword } from "../api/auth";

export default function ResetPassword() {
  const location = useLocation();
  const navigate = useNavigate();
  const { resetToken, email } = location.state || {};

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!resetToken) {
      navigate("/olvide-contrasena", { replace: true });
    }
  }, [resetToken, navigate]);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");

    if (password !== confirmPassword) {
      setError("Las contraseñas no coinciden.");
      return;
    }

    setLoading(true);
    try {
      await resetPassword({ resetToken, password });
      navigate("/contrasena-restablecida", { state: { email } });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  if (!resetToken) return null;

  return (
    <AuthLayout illustration="chat">
      <h1>Restablecer Contraseña</h1>
      <p className="auth-subtitle">Crea una nueva contraseña segura para tu cuenta.</p>

      <FormMessage type="error">{error}</FormMessage>

      <form className="auth-form" onSubmit={handleSubmit}>
        <PasswordField
          label="Nueva Contraseña"
          required
          minLength={8}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="••••••••"
        />
        <p className="auth-subtitle" style={{ margin: "-8px 0 0", fontSize: 12 }}>
          Mínimo 8 caracteres, con mayúsculas, minúsculas y números.
        </p>
        <PasswordField
          label="Confirmar Contraseña"
          required
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          placeholder="••••••••"
        />

        <PrimaryButton type="submit" loading={loading}>
          Confirmar Contraseña
        </PrimaryButton>
      </form>
    </AuthLayout>
  );
}
