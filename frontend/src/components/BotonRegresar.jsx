import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { rutaInicial } from "../utils/roles";
import "../styles/BotonRegresar.css";

/**
 * Botón "Regresar" reutilizable. Uso: <BotonRegresar />
 *
 * - Hay historial dentro de la app  -> vuelve a la pantalla anterior (navigate(-1)).
 * - Se abrió la pantalla directamente (enlace, recarga, pestaña nueva) -> va a `fallback`,
 *   para no sacar a la persona de la aplicación.
 *
 * Props opcionales:
 *   to        ruta fija (ignora el historial)
 *   fallback  destino cuando no hay historial (por defecto: inicio según el rol, o "/")
 *   tono      "claro" (texto claro, fondos oscuros; por defecto) | "oscuro" (fondos claros)
 *   label     texto del botón
 */
export default function BotonRegresar({ to, fallback, tono = "claro", label = "Regresar", className = "" }) {
  const navigate = useNavigate();
  const location = useLocation();
  const { usuario } = useAuth();

  const destinoPorDefecto = fallback ?? (usuario ? rutaInicial(usuario.rol) : "/");

  function regresar() {
    if (to) {
      navigate(to);
    } else if (location.key !== "default") {
      navigate(-1);
    } else {
      navigate(destinoPorDefecto, { replace: true });
    }
  }

  return (
    <button
      type="button"
      className={`boton-regresar boton-regresar--${tono} ${className}`.trim()}
      onClick={regresar}
      aria-label={label}
    >
      <span aria-hidden="true">←</span> {label}
    </button>
  );
}
