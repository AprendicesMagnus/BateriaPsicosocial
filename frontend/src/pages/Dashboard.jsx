import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "../styles/dashboard.css";
import { useAuth } from "../context/AuthContext";
import { fetchIndicadores } from "../api/indicadores";
import { fetchAnalisisPredictivo } from "../api/prediccion";
import { generarInformeAgrupado, descargarInforme } from "../api/informes";

const LABEL_NIVEL = {
  SIN_RIESGO: "Sin Riesgo",
  BAJO: "Bajo",
  MEDIO: "Medio",
  ALTO: "Alto",
  MUY_ALTO: "Muy Alto",
};

export default function Dashboard() {
  const { usuario, token, cerrarSesion } = useAuth();
  const navigate = useNavigate();

  const [mostrarModal, setMostrarModal] = useState(false);
  const [indicadores, setIndicadores] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState(null);

  const [mensajeDescarga, setMensajeDescarga] = useState(null);

  useEffect(() => {
    if (token) {
      cargarDatosIndicadores();
    }
  }, [token]);

  async function cargarDatosIndicadores() {
    setCargando(true);
    setError(null);
    try {
      const data = await fetchIndicadores(token);
      setIndicadores(data);
    } catch (err) {
      setError(err.message || "Ocurrió un error al cargar los indicadores.");
      setIndicadores(null);
    } finally {
      setCargando(false);
    }
  }

  function handleLogout() {
    cerrarSesion();
    navigate("/");
  }

  const calcularNivelPrevalente = () => {
    if (!indicadores?.distribucionRiesgo) return { nivel: "—", total: 0 };
    const dist = indicadores.distribucionRiesgo;
    let maxNivel = "SIN_RIESGO";
    let maxVal = -1;
    let totalResp = 0;

    Object.entries(dist).forEach(([nivel, val]) => {
      totalResp += val;
      if (val > maxVal) {
        maxVal = val;
        maxNivel = nivel;
      }
    });

    return {
      nivel: LABEL_NIVEL[maxNivel] || maxNivel,
      total: totalResp,
    };
  };

  const nivelPrevalente = calcularNivelPrevalente();

  const calcularPorcentajesRiesgo = () => {
    if (!indicadores?.distribucionRiesgo) return [];
    const dist = indicadores.distribucionRiesgo;
    const total = Object.values(dist).reduce((acc, v) => acc + v, 0);
    if (total === 0) {
      return Object.keys(dist).map((k) => [LABEL_NIVEL[k] || k, "0%"]);
    }
    return Object.entries(dist).map(([k, v]) => [
      LABEL_NIVEL[k] || k,
      `${Math.round((v / total) * 100)}%`,
    ]);
  };

  const distribucionPorcentual = calcularPorcentajesRiesgo();

  return (
    <div className="dashboard">
      <aside className="sidebar">
        <div className="sidebar__logo">
          <img
            src="/logob1.png"
            alt="Magnus"
            style={{ height: 70, marginRight: "auto" }}
          />
        </div>

        <nav className="sidebar__menu">
          <button
            className="menu-item active"
            type="button"
            onClick={() => navigate("/dashboard")}
          >
            <span>▣</span>
            Dashboard
          </button>

          <button
            className="menu-item"
            type="button"
            onClick={() => navigate("/cuestionario-estres")}
          >
            <span>☑</span>
            Cuestionario
          </button>

          <button
            className="menu-item"
            type="button"
            onClick={() => navigate("/panel")}
          >
            <span>⚙</span>
            Panel Admin
          </button>

          <button
            className="menu-item"
            type="button"
            onClick={handleLogout}
          >
            <span>✕</span>
            Cerrar sesión
          </button>
        </nav>

        <div className="sidebar__footer">
          <div className="footer-icon">◇</div>
          <span>
            Tu bienestar también
            <br />
            es parte del trabajo
          </span>
        </div>
      </aside>

      <main className="dashboard__main">
        <header className="dashboard__header">
          <div>
            <h1>Bienvenido, {usuario?.nombre || "Usuario"}</h1>
            <p>Tu bienestar también es parte del trabajo</p>
          </div>

          <div className="profile" aria-label="Perfil de usuario">
            <img
              src="/icono.png"
              alt="Magnus"
              style={{ height: 60, marginRight: "auto" }}
            />
          </div>
        </header>

        <section className="welcome-card">
          <div className="welcome-icon">ⓘ</div>

          <div className="welcome-text">
            <h2>Batería Psicológica de Riesgo Psicosocial</h2>
            <p>
              Sistema para conocer y medir aspectos del estado emocional,
              nivel de estrés y factores del entorno laboral (Resolución 2764 de 2022).
            </p>
          </div>

          <button
            className="welcome-button"
            type="button"
            onClick={() => setMostrarModal(true)}
            aria-label="Seleccionar cuestionario"
          >
            ✓
          </button>
        </section>

        {error && (
          <p className="error-text">
            No se pudieron cargar los indicadores del servidor: {error}
          </p>
        )}

        {mensajeDescarga && (
          <p className="error-text" style={{ background: "#e0f2fe", color: "#0369a1" }}>
            {mensajeDescarga}
          </p>
        )}

        <section className="dashboard-grid">
          <div className="chart-card">
            <div className="card-title">
              <div>
                <h3>Distribución de Riesgo Psicosocial</h3>
                <p>Niveles consolidados a nivel organizacional</p>
              </div>

              <div className="legend">
                <span>
                  <i className="dot green"></i>
                  Sin Riesgo / Bajo
                </span>
                <span>
                  <i className="dot orange"></i>
                  Alto / Muy Alto
                </span>
              </div>
            </div>

            <div className="chart">
              {cargando ? (
                <p className="chart-loading">Cargando indicadores reales...</p>
              ) : indicadores?.anonimizado ? (
                <div style={{ padding: "30px 20px", textAlign: "center", color: "#64748b" }}>
                  <p style={{ fontWeight: 600, fontSize: "15px", marginBottom: "8px" }}>
                    Datos Anonimizados
                  </p>
                  <p style={{ fontSize: "13px" }}>
                    {indicadores.mensajeAnonimato ||
                      "Se requiere un mínimo de 5 participantes completados para desglosar la gráfica de riesgo."}
                  </p>
                </div>
              ) : (
                <DistribucionRiesgoChart distribucion={indicadores?.distribucionRiesgo} />
              )}
            </div>
          </div>

          <div className="side-card population-card">
            <p>Población Evaluada</p>
            <strong>
              {cargando
                ? "…"
                : `${indicadores?.participacion?.totalCompletados ?? 0} / ${indicadores?.participacion?.totalAsignados ?? 0}`}
            </strong>
            <span className="increase">
              {cargando ? "" : `${indicadores?.participacion?.tasaPorcentaje ?? 0}% participación`}
            </span>
          </div>

          <div className="side-card risk-card">
            <h3>Nivel de riesgo prevalente</h3>
            <div className="risk-circle">
              <div>
                <strong>
                  {cargando
                    ? "…"
                    : indicadores?.anonimizado
                    ? "Anonimizado"
                    : nivelPrevalente.nivel}
                </strong>
                <small>
                  {cargando
                    ? ""
                    : indicadores?.anonimizado
                    ? "Grupo pequeño (<5)"
                    : `${nivelPrevalente.total} dimensiones medidas`}
                </small>
              </div>
            </div>
          </div>
        </section>

        <section className="indicators">
          <IndicatorCard
            title="Evaluaciones Registradas"
            subtitle={`${indicadores?.totalEvaluaciones ?? 0} evaluaciones totales`}
            active={true}
            values={[
              ["Finalizadas", `${indicadores?.evaluacionesPorEstado?.FINALIZADA ?? 0}`],
              ["En Curso", `${indicadores?.evaluacionesPorEstado?.EN_CURSO ?? 0}`],
              ["Borrador", `${indicadores?.evaluacionesPorEstado?.BORRADOR ?? 0}`],
            ]}
          />

          <IndicatorCard
            title="Desglose Nivel de Riesgo"
            subtitle={
              indicadores?.anonimizado
                ? "Información restringida por anonimato"
                : "Distribución porcentual por categoría"
            }
            active={false}
            values={
              indicadores?.anonimizado
                ? [
                    ["Información", "Protegida"],
                    ["Anonimato", "Mínimo 5"],
                  ]
                : distribucionPorcentual.length > 0
                ? distribucionPorcentual
                : [
                    ["Sin Riesgo", "—"],
                    ["Bajo", "—"],
                    ["Medio", "—"],
                    ["Alto", "—"],
                  ]
            }
          />

          <IndicatorCard
            title="Organizaciones Atendidas"
            subtitle={`${indicadores?.totalOrganizaciones ?? 0} organización(es)`}
            active={false}
            values={[
              ["Tasa Participación", `${indicadores?.participacion?.tasaPorcentaje ?? 0}%`],
              ["Completados", `${indicadores?.participacion?.totalCompletados ?? 0}`],
              ["Pendientes", `${(indicadores?.participacion?.totalAsignados ?? 0) - (indicadores?.participacion?.totalCompletados ?? 0)}`],
            ]}
          />
        </section>

        <section className="responders-card">
          <h3>Participación y Resumen de Cuestionarios</h3>
          <p>
            {cargando
              ? "Cargando métricas..."
              : `Total de ${indicadores?.participacion?.totalCompletados ?? 0} participante(s) han completado sus evaluaciones.`}
          </p>

          {cargando && <p className="chart-loading">Cargando estado de cuestionarios...</p>}

          {!cargando && indicadores?.anonimizado && (
            <div style={{ padding: "16px", background: "#f8fafc", borderRadius: "8px", border: "1px solid #e2e8f0", margin: "12px 0" }}>
              <p style={{ margin: 0, fontSize: "14px", color: "#475569" }}>
                🔒 <strong>Resguardo de Privacidad:</strong> Conforme a la Resolución 2764 de 2022 del Ministerio del Trabajo, los resultados individuales se mantienen strictly confidenciales y anonimizados cuando el grupo evaluado es inferior a 5 personas.
              </p>
            </div>
          )}

          {!cargando && !indicadores?.anonimizado && (
            <div className="table-wrap">
              <table className="responders-table">
                <thead>
                  <tr>
                    <th>Métrica de Participación</th>
                    <th>Valor Registrado</th>
                    <th>Estado</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>Participantes Asignados Totales</td>
                    <td>{indicadores?.participacion?.totalAsignados ?? 0}</td>
                    <td>
                      <span className="risk-badge bajo">Registrados</span>
                    </td>
                  </tr>
                  <tr>
                    <td>Cuestionarios Completados</td>
                    <td>{indicadores?.participacion?.totalCompletados ?? 0}</td>
                    <td>
                      <span className="risk-badge bajo">Completados</span>
                    </td>
                  </tr>
                  <tr>
                    <td>Tasa Global de Respuesta</td>
                    <td>{indicadores?.participacion?.tasaPorcentaje ?? 0}%</td>
                    <td>
                      <span
                        className={`risk-badge ${
                          (indicadores?.participacion?.tasaPorcentaje ?? 0) >= 80 ? "bajo" : "medio"
                        }`}
                      >
                        {(indicadores?.participacion?.tasaPorcentaje ?? 0) >= 80 ? "Óptimo" : "En seguimiento"}
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          )}
        </section>
      </main>

      {mostrarModal && (
        <div className="modal-overlay" onClick={() => setMostrarModal(false)}>
          <div className="questionnaire-modal" onClick={(e) => e.stopPropagation()}>
            <button
              className="modal-close"
              type="button"
              onClick={() => setMostrarModal(false)}
              aria-label="Cerrar ventana"
            >
              ×
            </button>

            <div className="modal-icon">
              <img
                src="/logob1.png"
                alt="Magnus"
                style={{ height: 60, marginRight: "auto" }}
              />
            </div>

            <h2>Cuestionarios de Riesgo Psicosocial</h2>
            <p>
              Selecciona el módulo que deseas realizar para continuar con la evaluación.
            </p>

            <div className="questionnaire-options">
              <button type="button" onClick={() => navigate("/cuestionario-estres")}>
                <strong>Cuestionario de Estrés</strong>
                <span>Evaluación de síntomas fisiológicos y psicoemocionales.</span>
              </button>
            </div>

            <button
              className="modal-main-button"
              type="button"
              onClick={() => navigate("/cuestionario-estres")}
            >
              Ir a cuestionarios
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function DistribucionRiesgoChart({ distribucion }) {
  const width = 700;
  const height = 220;
  const paddingX = 40;
  const paddingY = 30;

  if (!distribucion) {
    return <p className="chart-loading">Sin datos de distribución disponibles.</p>;
  }

  const niveles = [
    { clave: "SIN_RIESGO", etiqueta: "Sin Riesgo", color: "#059669" },
    { clave: "BAJO", etiqueta: "Bajo", color: "#1d4ed8" },
    { clave: "MEDIO", etiqueta: "Medio", color: "#b45309" },
    { clave: "ALTO", etiqueta: "Alto", color: "#c2410c" },
    { clave: "MUY_ALTO", etiqueta: "Muy Alto", color: "#b91c1c" },
  ];

  const valores = niveles.map((n) => distribucion[n.clave] || 0);
  const maxVal = Math.max(...valores, 1);

  const barWidth = 60;
  const gap = (width - paddingX * 2 - barWidth * niveles.length) / (niveles.length - 1);

  return (
    <svg viewBox={`0 0 ${width} ${height + 30}`} width="100%" role="img" aria-label="Gráfica de distribución de riesgo">
      {niveles.map((n, i) => {
        const val = distribucion[n.clave] || 0;
        const x = paddingX + i * (barWidth + gap);
        const barHeight = (val / maxVal) * (height - paddingY * 2);
        const y = height - paddingY - barHeight;

        return (
          <g key={n.clave}>
            <rect
              x={x}
              y={y}
              width={barWidth}
              height={Math.max(barHeight, 4)}
              fill={n.color}
              rx="4"
            />
            <text
              x={x + barWidth / 2}
              y={y - 6}
              fontSize="12"
              fontWeight="bold"
              textAnchor="middle"
              fill="#1e293b"
            >
              {val}
            </text>
            <text
              x={x + barWidth / 2}
              y={height + 16}
              fontSize="11"
              textAnchor="middle"
              fill="#64748b"
            >
              {n.etiqueta}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

function IndicatorCard({ title, subtitle, values, active, onClick }) {
  return (
    <div
      className={`indicator-card ${active ? "indicator-active" : ""}`}
      onClick={onClick}
      role={onClick ? "button" : undefined}
    >
      <div className="indicator-header">
        <div>
          <h3>{title}</h3>
          <p>{subtitle}</p>
        </div>
        {active && <span className="active-badge">Activo</span>}
      </div>

      <div className="indicator-values">
        {values.map(([name, val]) => (
          <div className="indicator-row" key={name}>
            <span>{name}</span>
            <div className="progress">
              <div
                className="progress-fill bajo"
                style={{
                  width: val.includes("%") ? val : "60%",
                }}
              ></div>
            </div>
            <small>{val}</small>
          </div>
        ))}
      </div>
    </div>
  );
}