import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { rutaEnlaceGuardado } from "../api/enlaces";

export default function ProtectedRoute({ children }) {
  const { token, usuario, loading } = useAuth();

  if (loading) return null;
  if (!token) return <Navigate to="/iniciar-sesion" replace />;
  // El paciente del enlace solo responde la batería: las páginas internas (dashboard, reportes...)
  // lo devuelven a su enlace, que muestra "Continuar" o el agradecimiento final
  if (usuario?.esInvitado) return <Navigate to={rutaEnlaceGuardado()} replace />;

  return children;
}
