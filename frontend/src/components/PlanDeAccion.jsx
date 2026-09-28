import { useState, useEffect } from "react";
import { fetchSeguimientosRecomendaciones, guardarSeguimientoRecomendacion } from "../api/seguimiento";

const ESTADOS = [
  { clave: "PENDIENTE", etiqueta: "Pendiente", color: "#64748B", bg: "#F1F5F9" },
  { clave: "EN_PROGRESO", etiqueta: "En Progreso", color: "#D97706", bg: "#FEF3C7" },
  { clave: "IMPLEMENTADA", etiqueta: "Implementada", color: "#059669", bg: "#D1FAE5" },
];

export default function PlanDeAccion({ token, organizacionId }) {
  const [seguimientos, setSeguimientos] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState(null);
  const [guardandoId, setGuardandoId] = useState(null);

  useEffect(() => {
    if (token) {
      cargarSeguimientos();
    }
  }, [token, organizacionId]);

  async function cargarSeguimientos() {
    setCargando(true);
    setError(null);
    try {
      const data = await fetchSeguimientosRecomendaciones(token, organizacionId);
      setSeguimientos(data);
    } catch (err) {
      setError(err.message || "Error al cargar el plan de acción / recomendaciones.");
    } finally {
      setCargando(false);
    }
  }

  async function handleCambiarEstado(recomendacionId, nuevoEstado) {
    setGuardandoId(recomendacionId);
    try {
      await guardarSeguimientoRecomendacion(token, {
        organizacionId,
        recomendacionId,
        estado: nuevoEstado,
      });
      await cargarSeguimientos();
    } catch (err) {
      alert(`Error al actualizar estado: ${err.message}`);
    } finally {
      setGuardandoId(null);
    }
  }

  if (cargando) {
    return (
      <div style={{ padding: "20px", textAlign: "center", color: "#64748b" }}>
        Cargando plan de acción y recomendaciones...
      </div>
    );
  }

  return (
    <div style={{ background: "#ffffff", padding: "24px", borderRadius: "12px", border: "1px solid #E2E8F0", marginTop: "24px" }}>
      <div style={{ marginBottom: "20px" }}>
        <h2 style={{ fontSize: "20px", color: "#1E293B", margin: "0 0 6px 0" }}>
          📋 Plan de Acción — Seguimiento de Recomendaciones (SST)
        </h2>
        <p style={{ fontSize: "14px", color: "#64748B", margin: 0 }}>
          Gestión del estado de implementación de las recomendaciones preventivas y correctivas por organización.
        </p>
      </div>

      {error && (
        <div style={{ padding: "12px", background: "#FEF2F2", color: "#991B1B", borderRadius: "6px", marginBottom: "16px" }}>
          ⚠️ {error}
        </div>
      )}

      {seguimientos.length === 0 ? (
        <div style={{ padding: "24px", textAlign: "center", background: "#F8FAFC", borderRadius: "8px", color: "#64748B" }}>
          <p style={{ margin: 0, fontWeight: 500 }}>No hay recomendaciones en seguimiento registradas aún.</p>
          <small>Al clasificar dimensiones en riesgo, se habilitan las acciones de intervención.</small>
        </div>
      ) : (
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "14px" }}>
            <thead>
              <tr style={{ background: "#F1F5F9", textAlign: "left" }}>
                <th style={{ padding: "12px", borderBottom: "2px solid #CBD5E1" }}>Dimensión</th>
                <th style={{ padding: "12px", borderBottom: "2px solid #CBD5E1" }}>Recomendación / Título</th>
                <th style={{ padding: "12px", borderBottom: "2px solid #CBD5E1" }}>Nivel Riesgo</th>
                <th style={{ padding: "12px", borderBottom: "2px solid #CBD5E1" }}>Estado Actual</th>
                <th style={{ padding: "12px", borderBottom: "2px solid #CBD5E1" }}>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {seguimientos.map((item) => {
                const rec = item.recomendacion || {};
                const estadoObj = ESTADOS.find((e) => e.clave === item.estado) || ESTADOS[0];

                return (
                  <tr key={item.id} style={{ borderBottom: "1px solid #E2E8F0" }}>
                    <td style={{ padding: "12px", fontWeight: "600", color: "#1E3A8A" }}>
                      {rec.dimension || "—"}
                    </td>
                    <td style={{ padding: "12px" }}>
                      <strong style={{ display: "block", color: "#1E293B" }}>{rec.titulo}</strong>
                      <span style={{ fontSize: "12px", color: "#64748B" }}>{rec.descripcion}</span>
                    </td>
                    <td style={{ padding: "12px" }}>
                      <span
                        style={{
                          padding: "4px 8px",
                          borderRadius: "4px",
                          fontSize: "12px",
                          fontWeight: "600",
                          background: rec.nivel === "MUY_ALTO" ? "#FEE2E2" : "#FFEDD5",
                          color: rec.nivel === "MUY_ALTO" ? "#991B1B" : "#C2410C",
                        }}
                      >
                        {rec.nivel ? rec.nivel.replace("_", " ") : "—"}
                      </span>
                    </td>
                    <td style={{ padding: "12px" }}>
                      <span
                        style={{
                          padding: "4px 10px",
                          borderRadius: "12px",
                          fontSize: "12px",
                          fontWeight: "bold",
                          background: estadoObj.bg,
                          color: estadoObj.color,
                        }}
                      >
                        {estadoObj.etiqueta}
                      </span>
                    </td>
                    <td style={{ padding: "12px" }}>
                      <select
                        value={item.estado}
                        disabled={guardandoId === item.recomendacionId}
                        onChange={(e) => handleCambiarEstado(item.recomendacionId, e.target.value)}
                        style={{
                          padding: "6px 10px",
                          borderRadius: "6px",
                          border: "1px solid #CBD5E1",
                          background: "white",
                          fontSize: "13px",
                          cursor: "pointer",
                        }}
                      >
                        {ESTADOS.map((est) => (
                          <option key={est.clave} value={est.clave}>
                            {est.etiqueta}
                          </option>
                        ))}
                      </select>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
