import { useEffect, useState } from "react";
import { fetchEvolucionPanel } from "../api/panel";
import "../styles/Panel.css";
import "../styles/PanelAcciones.css";

const METRICAS = [
  { clave: "usuariosNuevos", label: "Usuarios nuevos" },
  { clave: "evaluacionesCreadas", label: "Evaluaciones creadas" },
  { clave: "encuestasCompletadas", label: "Encuestas completadas" },
  { clave: "comprasPagadas", label: "Compras pagadas" },
  { clave: "valorComprado", label: "Valor comprado", esMoneda: true },
];

const formatoCOP = new Intl.NumberFormat("es-CO", {
  style: "currency",
  currency: "COP",
  maximumFractionDigits: 0,
});

export default function PanelEvolucion({ token }) {
  const [mesesData, setMesesData] = useState([]);
  const [metrica, setMetrica] = useState("usuariosNuevos");
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let activo = true;
    setCargando(true);
    setError(null);
    fetchEvolucionPanel(token, 12)
      .then((res) => {
        if (!activo) return;
        setMesesData(res?.meses || []);
      })
      .catch((err) => {
        if (!activo) return;
        setError(err.message || "No se pudo cargar la evolución mensual.");
      })
      .finally(() => {
        if (activo) setCargando(false);
      });
    return () => {
      activo = false;
    };
  }, [token]);

  if (cargando) {
    return (
      <section className="adm-card">
        <p style={{ padding: "24px", color: "var(--adm-muted, #5b6478)" }}>Cargando...</p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="adm-card">
        <div className="plan-mensaje plan-mensaje--error" style={{ margin: "16px" }}>
          {error}
        </div>
      </section>
    );
  }

  const todoCero = mesesData.every(
    (m) =>
      m.usuariosNuevos === 0 &&
      m.evaluacionesCreadas === 0 &&
      m.encuestasCompletadas === 0 &&
      m.comprasPagadas === 0 &&
      m.valorComprado === 0
  );

  const metricaActual = METRICAS.find((m) => m.clave === metrica) || METRICAS[0];
  const valores = mesesData.map((d) => d[metrica] || 0);
  const maxVal = Math.max(...valores, 0);

  const svgWidth = 800;
  const svgHeight = 240;
  const paddingX = 40;
  const paddingBottom = 40;
  const paddingTop = 30;
  const chartHeight = svgHeight - paddingTop - paddingBottom;
  const n = mesesData.length || 1;
  const step = (svgWidth - paddingX * 2) / n;
  const barWidth = Math.max(12, Math.min(40, step * 0.55));

  return (
    <section className="adm-card">
      <div className="adm-card__head">
        <div>
          <h2>Evolución mensual</h2>
          <span>Actividad del sistema en los últimos 12 meses</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <label htmlFor="selector-metrica" style={{ fontSize: "13px", fontWeight: "600", color: "var(--adm-muted, #5b6478)" }}>
            Métrica:
          </label>
          <select
            id="selector-metrica"
            value={metrica}
            onChange={(e) => setMetrica(e.target.value)}
            style={{
              padding: "7px 12px",
              borderRadius: "8px",
              border: "1px solid var(--adm-line, #e3e8ef)",
              background: "#ffffff",
              fontSize: "13px",
              color: "var(--adm-ink, #1f2a4d)",
              fontWeight: "600",
            }}
          >
            {METRICAS.map((m) => (
              <option key={m.clave} value={m.clave}>
                {m.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {todoCero ? (
        <p style={{ padding: "32px", textAlign: "center", color: "var(--adm-muted, #5b6478)", fontSize: "14px" }}>
          Aún no hay actividad registrada en este periodo.
        </p>
      ) : (
        <div style={{ margin: "20px 0", overflowX: "auto" }}>
          <svg
            viewBox={`0 0 ${svgWidth} ${svgHeight}`}
            style={{ width: "100%", minWidth: "600px", height: "auto", display: "block" }}
          >
            <line
              x1={paddingX - 10}
              y1={paddingTop + chartHeight}
              x2={svgWidth - paddingX + 10}
              y2={paddingTop + chartHeight}
              stroke="#cbd5e1"
              strokeWidth="1"
            />
            {mesesData.map((d, i) => {
              const val = d[metrica] || 0;
              const h = maxVal > 0 ? (val / maxVal) * chartHeight : 0;
              const x = paddingX + i * step + (step - barWidth) / 2;
              const y = paddingTop + chartHeight - h;
              const textoVal = metricaActual.esMoneda ? formatoCOP.format(val) : val;

              return (
                <g key={d.mes}>
                  <rect
                    x={x}
                    y={y}
                    width={barWidth}
                    height={Math.max(h, val > 0 ? 3 : 0)}
                    rx="4"
                    fill="#1e3a8a"
                  >
                    <title>{`${d.etiqueta}: ${textoVal}`}</title>
                  </rect>
                  {val > 0 && (
                    <text
                      x={x + barWidth / 2}
                      y={y - 6}
                      textAnchor="middle"
                      fontSize={metricaActual.esMoneda ? "9.5" : "11"}
                      fontWeight="700"
                      fill="#1e293b"
                    >
                      {textoVal}
                    </text>
                  )}
                  <text
                    x={x + barWidth / 2}
                    y={svgHeight - 14}
                    textAnchor="middle"
                    fontSize="11"
                    fill="#64748b"
                  >
                    {d.etiqueta}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>
      )}

      <div className="adm-tabla-wrap" style={{ marginTop: "16px" }}>
        <table className="adm-tabla adm-tabla--ancha">
          <thead>
            <tr>
              <th>Mes</th>
              <th>Usuarios nuevos</th>
              <th>Evaluaciones creadas</th>
              <th>Encuestas completadas</th>
              <th>Compras pagadas</th>
              <th>Valor comprado</th>
            </tr>
          </thead>
          <tbody>
            {mesesData.map((d) => (
              <tr key={d.mes}>
                <td>
                  <strong>{d.etiqueta}</strong>
                  <span style={{ display: "block", fontSize: "11px", color: "var(--adm-muted, #5b6478)" }}>
                    {d.mes}
                  </span>
                </td>
                <td>{d.usuariosNuevos}</td>
                <td>{d.evaluacionesCreadas}</td>
                <td>{d.encuestasCompletadas}</td>
                <td>{d.comprasPagadas}</td>
                <td>{formatoCOP.format(d.valorComprado || 0)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
