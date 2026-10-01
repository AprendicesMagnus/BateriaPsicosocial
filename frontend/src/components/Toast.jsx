import "../styles/Toast.css";

// Aviso flotante. `duracion` (ms) solo controla la barra de progreso;
// quien lo usa decide cuándo dejar de mostrarlo.
export default function Toast({ mensaje, tipo = "info", duracion = 3000 }) {
  if (!mensaje) return null;
  return (
    <div className={`toast toast--${tipo}`} role="status" aria-live="polite">
      <span className="toast__icono" aria-hidden="true">
        {tipo === "error" ? "!" : "i"}
      </span>
      <span className="toast__texto">{mensaje}</span>
      <span className="toast__barra" style={{ animationDuration: `${duracion}ms` }} />
    </div>
  );
}
