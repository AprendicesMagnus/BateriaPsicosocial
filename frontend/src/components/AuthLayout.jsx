import { Link } from "react-router-dom";
import IllustrationPanel from "./IllustrationPanel";
import "../styles/auth.css";

// volverA: ruta opcional. Si se pasa, muestra un botón "Volver" arriba del formulario.
export default function AuthLayout({ illustration = "network", volverA, children }) {
  return (
    <div className="auth-shell">
      <div className="auth-card">
        <div className="auth-side">
          <IllustrationPanel variant={illustration} />
        </div>
        <div className="auth-form-panel">
          {volverA && (
            <Link to={volverA} className="auth-back" aria-label="Volver al inicio">
              <span aria-hidden="true">←</span> Volver
            </Link>
          )}
          {children}
        </div>
      </div>
    </div>
  );
}