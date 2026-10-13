import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { rutaInicial, rutaPermitidaParaRol } from "../utils/roles";

// Responsable SST: trabaja desde el Dashboard. Las pantallas de empresas, tienda/pago y panel
// de administración lo devuelven a su Dashboard. Va dentro de <BrowserRouter>.
export default function RestriccionRolLimitado({ children }) {
  const { usuario } = useAuth();
  const { pathname } = useLocation();

  if (usuario && !rutaPermitidaParaRol(usuario.rol, pathname)) {
    return <Navigate to={rutaInicial(usuario.rol)} replace />;
  }
  return children;
}
