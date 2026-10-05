import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { rutaEnlaceGuardado } from "../api/enlaces";
import { rutaInicial } from "../utils/roles";

// roles (opcional): lista de roles que pueden entrar; el resto vuelve a su inicio.
export default function ProtectedRoute({ children, roles }) {
  const { token, usuario, loading } = useAuth();

  if (loading) return null;
  if (!token) return <Navigate to="/iniciar-sesion" replace />;
  // El paciente del enlace solo responde la batería: las páginas internas (dashboard, reportes...)
  // lo devuelven a su enlace, que muestra "Continuar" o el agradecimiento final
  if (usuario?.esInvitado) return <Navigate to={rutaEnlaceGuardado()} replace />;

  if (roles && usuario && !roles.includes(usuario.rol)) {
    return <Navigate to={rutaInicial(usuario.rol)} replace />;
  }

  return children;
}
