import { useNavigate } from "react-router-dom";
import AuthLayout from "../components/AuthLayout";
import { PrimaryButton } from "../components/FormControls";

export default function ResetSuccessful() {
  const navigate = useNavigate();

  return (
    <AuthLayout illustration="success">
      <div className="success-panel">
        <h1>Tu contraseña ha sido restablecida</h1>
        <p>Ya puedes iniciar sesión con tu nueva contraseña.</p>
        <div style={{ marginTop: 20 }}>
          <PrimaryButton
            type="button"
            onClick={() =>
              navigate("/iniciar-sesion", {
                state: { message: "Contraseña restablecida. Inicia sesión con tu nueva contraseña." },
              })
            }
          >
            Continuar →
          </PrimaryButton>
        </div>
      </div>
    </AuthLayout>
  );
}
