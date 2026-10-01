import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { rutaPermitidaParaRol } from "../utils/roles";

// Usuario limitado (RESPONSABLE_SST): solo puede estar en Reportes (y su perfil).
// Cualquier otra ruta lo devuelve a /reportes. Va dentro de <BrowserRouter>.
export default function RestriccionRolLimitado({ children }) {
  const { usuario } = useAuth();
  const { pathname } = useLocation();

  if (usuario && !rutaPermitidaParaRol(usuario.rol, pathname)) {
    return <Navigate to="/reportes" replace />;
  }
  return children;
}
