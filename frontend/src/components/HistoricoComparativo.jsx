import { useEffect, useState } from "react";
import { fetchHistoricoIndicadores } from "../api/indicadores";

const NIVELES_COLOR = {
  SIN_RIESGO: { bg: "#DEF7EC", text: "#03543F", label: "Sin Riesgo" },
  BAJO: { bg: "#E1EFFE", text: "#1E40AF", label: "Bajo" },
  MEDIO: { bg: "#FEF08A", text: "#713F12", label: "Medio" },
  ALTO: { bg: "#FDBA74", text: "#9A3412", label: "Alto" },
  MUY_ALTO: { bg: "#FCA5A5", text: "#991B1B", label: "Muy Alto" },
};

export default function HistoricoComparativo({ token, organizacionId }) {
  const [dataHistorica, setDataHistorica] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    cargarHistorico();
  }, [token, organizacionId]);

  async function cargarHistorico() {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchHistoricoIndicadores(token, organizacionId);
      setDataHistorica(data);
    } catch (err) {
      setError(err.message || "Error al cargar el histórico comparativo.");
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return <p style={{ color: "#64748B" }}>Cargando histórico comparativo BRP...</p>;
  }

  if (error) {
    return (
      <div style={{ padding: 16, background: "#FEF2F2", color: "#991B1B", borderRadius: 8, fontSize: 14 }}>
        ⚠️ {error}
      </div>
    );
  }

  const historico = dataHistorica?.historico || [];

  if (historico.length === 0) {
    return (
      <div style={{ background: "white", padding: 24, borderRadius: 12, border: "1px solid #E2E8F0" }}>
        <h3 style={{ fontSize: 18, color: "#1E293B", marginTop: 0, marginBottom: 8 }}>
          📈 Histórico Comparativo BRP
        </h3>
        <p style={{ color: "#64748B", fontSize: 14, margin: 0 }}>
          Aún no existen múltiples evaluaciones finalizadas y tabuladas en esta organización para comparar la tendencia histórica de riesgo.
        </p>
      </div>
    );
  }

  return (
    <div style={{ background: "white", padding: 24, borderRadius: 12, border: "1px solid #E2E8F0" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <div>
          <h3 style={{ fontSize: 18, color: "#1E293B", margin: 0 }}>
            📈 Histórico Comparativo BRP (Serie Temporal)
          </h3>
          <p style={{ fontSize: 13, color: "#64748B", margin: "4px 0 0 0" }}>
            Evolución del puntaje promedio de riesgo psicosocial a través de las evaluaciones.
          </p>
        </div>
        <button className="btn-secondary" onClick={cargarHistorico} style={{ fontSize: 12 }}>
          🔄 Actualizar
        </button>
      </div>

      {/* GRAFICO DE TENDENCIA DE BARRAS SIMPLE */}
      <div style={{ background: "#F8FAFC", padding: 20, borderRadius: 8, border: "1px solid #CBD5E1", marginBottom: 24 }}>
        <div style={{ fontSize: 13, fontWeight: "bold", color: "#1E3A8A", marginBottom: 16 }}>
          Tendencia del Puntaje Transformado Promedio (Menor puntaje = Menor riesgo)
        </div>
        <div style={{ display: "flex", gap: 24, alignItems: "flex-end", height: 160, paddingTop: 20, borderBottom: "2px solid #CBD5E1" }}>
          {historico.map((h, idx) => {
            const pctHeight = Math.min(100, Math.max(10, h.promedioPuntajeTransformado));
            const esUltimo = idx === historico.length - 1;
            const anterior = idx > 0 ? historico[idx - 1] : null;
            let variacion = null;
            if (anterior) {
              const diff = roundTwo(h.promedioPuntajeTransformado - anterior.promedioPuntajeTransformado);
              variacion = diff <= 0 ? `▼ ${Math.abs(diff)} pts (Mejoró)` : `▲ ${diff} pts (Aumentó riesgo)`;
            }

            return (
              <div key={h.evaluacionId} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", height: "100%" }}>
                <div style={{ fontSize: 12, fontWeight: "bold", color: "#1E293B", marginBottom: 4 }}>
                  {h.promedioPuntajeTransformado} pts
                </div>
                <div style={{ flex: 1, width: "100%", display: "flex", alignItems: "flex-end", justifyContent: "center" }}>
                  <div
                    style={{
                      width: "60%",
                      maxWidth: 60,
                      height: `${pctHeight}%`,
                      background: esUltimo ? "#1E3A8A" : "#64748B",
                      borderRadius: "6px 6px 0 0",
                      transition: "height 0.4s ease",
                    }}
                  />
                </div>
                <div style={{ fontSize: 11, fontWeight: "600", color: "#475569", marginTop: 8, textAlign: "center" }}>
                  {h.nombreEvaluacion}
                </div>
                {variacion && (
                  <div style={{ fontSize: 10, color: variacion.includes("Mejoró") ? "#059669" : "#DC2626", fontWeight: "bold" }}>
                    {variacion}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* TABLA COMPARATIVA DETALLADA */}
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13, textAlign: "left" }}>
        <thead>
          <tr style={{ background: "#F1F5F9", color: "#334155", borderBottom: "2px solid #CBD5E1" }}>
            <th style={{ padding: "10px 12px" }}>Evaluación</th>
            <th style={{ padding: "10px 12px" }}>Fecha</th>
            <th style={{ padding: "10px 12px" }}>Participantes</th>
            <th style={{ padding: "10px 12px" }}>Promedio R.P.</th>
            <th style={{ padding: "10px 12px" }}>Desglose Niveles</th>
          </tr>
        </thead>
        <tbody>
          {historico.map((item) => (
            <tr key={item.evaluacionId} style={{ borderBottom: "1px solid #E2E8F0" }}>
              <td style={{ padding: "12px", fontWeight: "600", color: "#1E293B" }}>{item.nombreEvaluacion}</td>
              <td style={{ padding: "12px", color: "#64748B" }}>{new Date(item.fecha).toLocaleDateString()}</td>
              <td style={{ padding: "12px", color: "#334155" }}>{item.totalParticipantes}</td>
              <td style={{ padding: "12px", fontWeight: "bold", color: "#1E3A8A" }}>
                {item.promedioPuntajeTransformado} pts
              </td>
              <td style={{ padding: "12px" }}>
                <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                  {Object.entries(item.distribucionNiveles || {}).map(([niv, count]) => {
                    if (count === 0) return null;
                    const conf = NIVELES_COLOR[niv] || { bg: "#F1F5F9", text: "#334155", label: niv };
                    return (
                      <span
                        key={niv}
                        style={{
                          background: conf.bg,
                          color: conf.text,
                          padding: "2px 8px",
                          borderRadius: 12,
                          fontSize: 11,
                          fontWeight: "bold",
                        }}
                      >
                        {conf.label}: {count}
                      </span>
                    );
                  })}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function roundTwo(num) {
  return Math.round(num * 100) / 100;
}
