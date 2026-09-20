import { useEffect, useState } from "react";
import { fetchEvaluaciones } from "../api/evaluaciones";

const ESTADO_BADGE = {
  PENDIENTE: { bg: "#FEF3C7", text: "#92400E", label: "Pendiente" },
  EN_PROGRESO: { bg: "#DBEAFE", text: "#1E40AF", label: "En Progreso" },
  COMPLETADA: { bg: "#D1FAE5", text: "#065F46", label: "Completada" },
  FINALIZADA: { bg: "#E2E8F0", text: "#475569", label: "Cerrada" },
};

export default function ListaEvaluacionesTrabajador({ token, onSeleccionarEvaluacion }) {
  const [evaluaciones, setEvaluaciones] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    cargar();
  }, [token]);

  async function cargar() {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchEvaluaciones(token);
      setEvaluaciones(data || []);
    } catch (err) {
      setError(err.message || "Error al cargar las evaluaciones asignadas.");
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return <p style={{ color: "#64748B" }}>Cargando evaluaciones asignadas...</p>;
  }

  if (error) {
    return (
      <div style={{ padding: 16, background: "#FEF2F2", color: "#991B1B", borderRadius: 8 }}>
        ⚠️ {error}
      </div>
    );
  }

  if (evaluaciones.length === 0) {
    return (
      <div style={{ background: "white", padding: 32, borderRadius: 12, border: "1px solid #E2E8F0", textAlign: "center" }}>
        <p style={{ color: "#64748B", fontSize: 15, margin: 0 }}>
          No tienes evaluaciones asignadas pendientes en este momento.
        </p>
      </div>
    );
  }

  return (
    <div style={{ display: "grid", gap: 16 }}>
      {evaluaciones.map((ev) => {
        const estadoInfo = ESTADO_BADGE[ev.estado] || { bg: "#F1F5F9", text: "#475569", label: ev.estado };
        return (
          <div
            key={ev.id}
            style={{
              background: "white",
              padding: 20,
              borderRadius: 12,
              border: "1px solid #E2E8F0",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              gap: 16,
              boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
            }}
          >
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
                <h3 style={{ margin: 0, fontSize: 17, color: "#1E293B" }}>{ev.nombre}</h3>
                <span
                  style={{
                    background: estadoInfo.bg,
                    color: estadoInfo.text,
                    fontSize: 12,
                    fontWeight: "bold",
                    padding: "2px 10px",
                    borderRadius: 12,
                  }}
                >
                  {estadoInfo.label}
                </span>
              </div>
              <p style={{ margin: 0, fontSize: 13, color: "#64748B" }}>
                ID Evaluación: <code style={{ fontSize: 11 }}>{ev.id}</code>
              </p>
            </div>

            <button
              className="btn-primary"
              onClick={() => onSeleccionarEvaluacion(ev.id)}
              style={{ flexShrink: 0 }}
            >
              {ev.estado === "COMPLETADA"
                ? "Ver Mis Resultados"
                : ev.estado === "EN_PROGRESO"
                ? "Continuar Cuestionario"
                : "Iniciar Cuestionario"}
            </button>
          </div>
        );
      })}
    </div>
  );
}
