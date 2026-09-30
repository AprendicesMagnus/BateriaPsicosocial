/**
 * Aviso que se muestra arriba de las preguntas de cada cuestionario.
 *
 * - Mientras se carga el cuestionario desde el backend: "Cargando cuestionario…".
 * - Si algo falla (no hay evaluación asignada, no se pudo guardar una respuesta,
 *   faltan preguntas al finalizar...): el mensaje de error en rojo.
 *
 * Existe para que el trabajador sepa cuándo sus respuestas NO se están guardando;
 * antes el error quedaba oculto y parecía que todo funcionaba.
 *
 * @param {{ cargando: boolean, error: string | null }} props Valores que devuelve useCuestionarioBackend.
 */
export default function AvisoCuestionario({ cargando, error }) {
  if (error) {
    return (
      <div role="alert" style={estilos.error}>
        <strong>No se están guardando tus respuestas.</strong> {error}
      </div>
    );
  }
  if (cargando) {
    return (
      <div role="status" style={estilos.cargando}>
        Cargando cuestionario…
      </div>
    );
  }
  return null;
}

// Estilos en línea para no depender de las hojas CSS de cada página
const estilos = {
  error: {
    background: "#FEE2E2",
    color: "#991B1B",
    border: "1px solid #FCA5A5",
    borderRadius: "8px",
    padding: "12px 16px",
    marginBottom: "16px",
    fontSize: "0.95rem",
  },
  cargando: {
    background: "#E1EFFE",
    color: "#1E40AF",
    border: "1px solid #BFDBFE",
    borderRadius: "8px",
    padding: "12px 16px",
    marginBottom: "16px",
    fontSize: "0.95rem",
  },
};
