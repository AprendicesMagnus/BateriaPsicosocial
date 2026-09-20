import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "../styles/dashboard.css";
import { useAuth } from "../context/AuthContext";
import { fetchIndicadores } from "../api/indicadores";
import { fetchAnalisisPredictivo } from "../api/prediccion";
import { generarInformeAgrupado, descargarInforme } from "../api/informes";

const CATEGORIAS = [
  { id: 1, nombre: "Estrés", totalPreguntas: 31, ruta: "/cuestionario-estres" },
  { id: 2, nombre: "Extralaboral A", totalPreguntas: 31, ruta: "/cuestionario-extralaboral" },
  { id: 3, nombre: "Intralaboral - Forma A", totalPreguntas: 123, ruta: "/cuestionario-intralaboral" },
  { id: 4, nombre: "Socio demográfico A", totalPreguntas: 31, ruta: "/ficha-datos-generales" },
];

const CATEGORIAS_B = [
  { id: 5, nombre: "Estrés B", totalPreguntas: 31, ruta: "/cuestionario-estresB" },
  { id: 6, nombre: "Extralaboral B", totalPreguntas: 31, ruta: "/cuestionario-extralaboralB" },
  { id: 7, nombre: "Intralaboral B", totalPreguntas: 123, ruta: "/cuestionario-intralaboralB" },
  { id: 8, nombre: "Socio demográfico B", totalPreguntas: 123, ruta: "/ficha-datos-generales" },
];

const CUESTIONARIOS_MODAL = [
  {
    clave: "estres",
    titulo: "Cuestionario de Estrés",
    descripcion: "Evaluación de síntomas relacionados con estrés.",
    rutaA: "/cuestionario-estres",
    rutaB: "/cuestionario-estresB",
  },
  {
    clave: "extralaboral",
    titulo: "Evaluación Extralaboral",
    descripcion: "Evaluación de factores externos al trabajo.",
    rutaA: "/cuestionario-extralaboral",
    rutaB: "/cuestionario-extralaboralB",
  },
  {
    clave: "intralaboral",
    titulo: "Evaluación Intralaboral",
    descripcion: "Evaluación de las condiciones dentro del entorno laboral.",
    rutaA: "/cuestionario-intralaboral",
    rutaB: "/cuestionario-intralaboralB",
  },
];

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
  const [cuestionarioSeleccionado, setCuestionarioSeleccionado] = useState(null);
  const [categoriaActivaId, setCategoriaActivaId] = useState(1);

  // 1. fetchIndicadores
  const [indicadores, setIndicadores] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState(null);

  // 2. fetchAnalisisPredictivo
  const [prediccion, setPrediccion] = useState(null);
  const [cargandoPrediccion, setCargandoPrediccion] = useState(false);
  const [errorPrediccion, setErrorPrediccion] = useState(null);

  // 3 & 4. generarInformeAgrupado, descargarInforme
  const [mensajeDescarga, setMensajeDescarga] = useState(null);
  const [generandoInforme, setGenerandoInforme] = useState(false);

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
      setError(err.message || "Ocurrió un error al cargar los indicadores de la base de datos.");
      setIndicadores(null);
    } finally {
      setCargando(false);
    }
  }

  async function handleEjecutarPrediccion(evaluacionId) {
    if (!evaluacionId) return;
    setCargandoPrediccion(true);
    setErrorPrediccion(null);
    try {
      const data = await fetchAnalisisPredictivo(token, evaluacionId);
      setPrediccion(data);
    } catch (err) {
      setErrorPrediccion(err.message || "No fue posible generar el análisis predictivo.");
      setPrediccion(null);
    } finally {
      setCargandoPrediccion(false);
    }
  }

  async function handleDescargarInforme() {
    setGenerandoInforme(true);
    setMensajeDescarga(null);
    try {
      const res = await generarInformeAgrupado(token, null, null, "PDF");
      if (res.id) {
        await descargarInforme(token, res.id);
        setMensajeDescarga("Informe generado y descargado correctamente.");
      } else {
        setMensajeDescarga("Informe solicitado con éxito.");
      }
    } catch (err) {
      setMensajeDescarga(err.message || "No se pudo generar el informe. Intenta nuevamente.");
    } finally {
      setGenerandoInforme(false);
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

  const cerrarModal = () => {
    setMostrarModal(false);
    setCuestionarioSeleccionado(null);
  };

  const elegirTipo = (ruta) => {
    cerrarModal();
    navigate(ruta);
  };

  return (
    <div className="dashboard">
      <aside className="sidebar">
        <div className="sidebar__logo">
          <img src="/logob1.png" alt="Magnus" style={{ height: 70, marginRight: "auto" }} />
        </div>

        <nav className="sidebar__menu">
          <button className="menu-item active" type="button" onClick={() => navigate("/dashboard")}>
            <span>▣</span>
            Dashboard
          </button>

          <button className="menu-item" type="button" onClick={() => navigate("/ficha-datos-generales")}>
            <span>☑</span>
            Cuestionario
          </button>

          <button className="menu-item" type="button" onClick={() => navigate("/panel")}>
            <span>⚙</span>
            Panel Admin
          </button>

          <button className="menu-item" type="button" onClick={handleLogout}>
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

          <div
            className="profile"
            aria-label="Perfil de usuario"
            onClick={() => navigate("/perfil")}
            style={{ cursor: "pointer" }}
          >
            <img src="/icono.png" alt="Magnus" style={{ height: 60, marginRight: "auto" }} />
          </div>
        </header>

        <section className="welcome-card">
          <div className="welcome-icon">ⓘ</div>

          <div className="welcome-text">
            <h2>Batería Psicológica de Riesgo Psicosocial</h2>
            <p>
              Sistema para conocer y medir aspectos del estado emocional, nivel de estrés y
              factores del entorno laboral (Resolución 2764 de 2022).
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

        {/* Pestañas de categorías del formulario A */}
        <div className="category-tabs">
          {CATEGORIAS.map((categoria) => (
            <button
              key={categoria.id}
              type="button"
              className={categoria.id === categoriaActivaId ? "selected" : ""}
              onClick={() => {
                setCategoriaActivaId(categoria.id);
                navigate(categoria.ruta);
              }}
              aria-pressed={categoria.id === categoriaActivaId}
            >
              {categoria.nombre}
              <small>{categoria.totalPreguntas} preguntas</small>
            </button>
          ))}
        </div>

        {/* Pestañas de categorías del formulario B */}
        <div className="category-tabs category-tabs--b" style={{ marginTop: 10 }}>
          {CATEGORIAS_B.map((categoria) => (
            <button
              key={categoria.id}
              type="button"
              className={categoria.id === categoriaActivaId ? "selected" : ""}
              onClick={() => {
                setCategoriaActivaId(categoria.id);
                navigate(categoria.ruta);
              }}
              aria-pressed={categoria.id === categoriaActivaId}
            >
              {categoria.nombre}
              <small>{categoria.totalPreguntas} preguntas</small>
            </button>
          ))}
        </div>

        {error && (
          <p className="error-text">No se pudieron cargar los indicadores del servidor: {error}</p>
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
                <p className="chart-loading">Cargando indicadores reales del servidor...</p>
              ) : indicadores?.anonimizado ? (
                <div style={{ padding: "30px 20px", textAlign: "center", color: "#64748b" }}>
                  <p style={{ fontWeight: 600, fontSize: "15px", marginBottom: "8px" }}>
                    🔒 Datos Anonimizados
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
                : `${indicadores?.participacion?.totalCompletados ?? 0} / ${
                    indicadores?.participacion?.totalAsignados ?? 0
                  }`}
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
                  {cargando ? "…" : indicadores?.anonimizado ? "Anonimizado" : nivelPrevalente.nivel}
                </strong>
                <small>
                  {cargando
                    ? ""
                    : indicadores?.anonimizado
                    ? "Grupo pequeño (<5)"
                    : `${nivelPrevalente.total} respuestas registradas`}
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
              [
                "Pendientes",
                `${
                  (indicadores?.participacion?.totalAsignados ?? 0) -
                  (indicadores?.participacion?.totalCompletados ?? 0)
                }`,
              ],
            ]}
          />
        </section>

        {/* =========================================================
            SECCIÓN DE ANÁLISIS PREDICTIVO CON IA (K-MEANS)
        ========================================================= */}
        <section className="responders-card" style={{ marginTop: "24px" }}>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              flexWrap: "wrap",
              gap: "8px",
            }}
          >
            <div>
              <h3>Análisis Predictivo (K-Means Clustering IA)</h3>
              <p style={{ margin: "4px 0 0", fontSize: "13px", color: "#64748b" }}>
                Identificación de perfiles de riesgo no supervisados y alertas tempranas en tiempo real.
              </p>
            </div>

            <button
              type="button"
              className="modal-main-button"
              onClick={() => handleEjecutarPrediccion(indicadores?.evaluacionId || "eval-actual")}
              disabled={cargandoPrediccion}
            >
              {cargandoPrediccion ? "Analizando con IA..." : "🤖 Analizar con IA (K-Means)"}
            </button>
          </div>

          {errorPrediccion && (
            <p className="error-text" style={{ marginTop: "12px" }}>
              {errorPrediccion}
            </p>
          )}

          {prediccion && (
            <div style={{ marginTop: "16px" }}>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
                  gap: "12px",
                  marginBottom: "16px",
                }}
              >
                {prediccion.perfilesClusterKMeans?.map((cluster) => (
                  <div
                    key={cluster.clusterId}
                    style={{
                      padding: "14px",
                      background: "#f8fafc",
                      borderRadius: "8px",
                      border: "1px solid #cbd5e1",
                    }}
                  >
                    <span style={{ fontSize: "12px", fontWeight: "bold", color: "#2563eb" }}>
                      Clúster #{cluster.clusterId} ({cluster.porcentajeGrupo}%)
                    </span>
                    <h4 style={{ margin: "6px 0", fontSize: "14px", color: "#1e293b" }}>
                      {cluster.etiqueta}
                    </h4>
                    <p style={{ margin: 0, fontSize: "12px", color: "#64748b" }}>
                      {cluster.numTrabajadores} trabajador(es) · Promedio: {cluster.promedioGlobalPuntaje} pts
                    </p>
                  </div>
                ))}
              </div>

              {prediccion.alertasTempranas?.length > 0 && (
                <div style={{ marginBottom: "16px" }}>
                  <h4 style={{ fontSize: "14px", color: "#b91c1c", marginBottom: "8px" }}>
                    ⚠️ Alertas Tempranas Identificadas ({prediccion.alertasTempranas.length})
                  </h4>
                  <ul style={{ margin: 0, paddingLeft: "20px", fontSize: "13px", color: "#475569" }}>
                    {prediccion.alertasTempranas.map((alerta, idx) => (
                      <li key={idx} style={{ marginBottom: "4px" }}>
                        <strong>[{alerta.nivelAlerta}]</strong> {alerta.mensaje}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* NOTA METODOLÓGICA Y ESTRATEGIA DE ENTRENAMIENTO */}
              <div
                style={{
                  padding: "16px",
                  background: "#f0fdf4",
                  borderRadius: "8px",
                  border: "1px solid #bbf7d0",
                  marginTop: "12px",
                }}
              >
                <p style={{ margin: "0 0 8px 0", fontSize: "13px", color: "#166534", fontWeight: 600 }}>
                  🤖 <strong>Nota Metodológica del Modelo:</strong>
                </p>
                <p style={{ margin: "0 0 10px 0", fontSize: "12px", color: "#15803d", lineHeight: "1.5" }}>
                  {prediccion.notaMetodologica}
                </p>

                <p style={{ margin: "0 0 4px 0", fontSize: "13px", color: "#166534", fontWeight: 600 }}>
                  ⚡ <strong>Estrategia de Entrenamiento:</strong>
                </p>
                <p style={{ margin: 0, fontSize: "12px", color: "#15803d", lineHeight: "1.5" }}>
                  {prediccion.estrategiaEntrenamiento}
                </p>
              </div>
            </div>
          )}
        </section>

        <section className="responders-card">
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              flexWrap: "wrap",
              gap: "8px",
            }}
          >
            <h3>Participación y Resumen de Cuestionarios</h3>

            <button
              type="button"
              className="modal-main-button"
              onClick={handleDescargarInforme}
              disabled={generandoInforme}
            >
              {generandoInforme ? "Generando informe..." : "Descargar informe"}
            </button>
          </div>

          <p>
            {cargando
              ? "Cargando métricas..."
              : `Total de ${indicadores?.participacion?.totalCompletados ?? 0} participante(s) han completado sus evaluaciones.`}
          </p>

          {cargando && <p className="chart-loading">Cargando estado de cuestionarios...</p>}

          {!cargando && indicadores?.anonimizado && (
            <div
              style={{
                padding: "16px",
                background: "#f8fafc",
                borderRadius: "8px",
                border: "1px solid #e2e8f0",
                margin: "12px 0",
              }}
            >
              <p style={{ margin: 0, fontSize: "14px", color: "#475569" }}>
                🔒 <strong>Resguardo de Privacidad:</strong> Conforme a la Resolución 2764 de 2022
                del Ministerio del Trabajo, los resultados individuales se mantienen estrictamente
                confidenciales y anonimizados cuando el grupo evaluado es inferior a 5 personas.
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
                        {(indicadores?.participacion?.tasaPorcentaje ?? 0) >= 80
                          ? "Óptimo"
                          : "En seguimiento"}
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
        <div className="modal-overlay" onClick={cerrarModal}>
          <div className="questionnaire-modal" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" type="button" onClick={cerrarModal} aria-label="Cerrar ventana">
              ×
            </button>

            {!cuestionarioSeleccionado ? (
              <>
                <div className="modal-icon">
                  <img
                    src="/logob1.png"
                    alt="Magnus"
                    style={{ height: 60, marginRight: "auto" }}
                  />
                </div>

                <h2>¿Qué cuestionario deseas realizar?</h2>
                <p>Selecciona el cuestionario que deseas realizar para continuar con la evaluación.</p>

                <div className="questionnaire-options">
                  {CUESTIONARIOS_MODAL.map((c) => (
                    <button key={c.clave} type="button" onClick={() => setCuestionarioSeleccionado(c)}>
                      <strong>{c.titulo}</strong>
                      <span>{c.descripcion}</span>
                    </button>
                  ))}
                </div>

                <button className="modal-main-button" type="button" onClick={() => navigate("/cuestionario-estres")}>
                  Ir a cuestionarios
                </button>
              </>
            ) : (
              <>
                <h2>{cuestionarioSeleccionado.titulo}</h2>
                <p>Selecciona la modalidad según el tipo de trabajador:</p>

                <div className="modal-type-buttons">
                  <button
                    type="button"
                    className="modal-type-btn"
                    onClick={() => elegirTipo(cuestionarioSeleccionado.rutaA)}
                  >
                    <strong>Forma A</strong>
                    <span>Para cargos de jefatura, profesionales o técnicos</span>
                  </button>

                  <button
                    type="button"
                    className="modal-type-btn"
                    onClick={() => elegirTipo(cuestionarioSeleccionado.rutaB)}
                  >
                    <strong>Forma B</strong>
                    <span>Para cargos de auxiliares u operarios</span>
                  </button>
                </div>
              </>
            )}
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
                  width: typeof val === "string" && val.includes("%") ? val : "60%",
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