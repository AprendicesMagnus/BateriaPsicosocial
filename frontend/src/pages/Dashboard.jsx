import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import "../styles/dashboard.css";

/* =========================================================
   CATEGORÍAS
========================================================= */

const CATEGORIAS = [
  { id: 1, nombre: "Estrés", totalPreguntas: 31 },
  { id: 2, nombre: "Extralaboral", totalPreguntas: 31 },
  { id: 3, nombre: "Intralaboral - Forma A", totalPreguntas: 123 },
  { id: 4, nombre: "Socio demográfico", totalPreguntas: 31 },
];

/* =========================================================
   DATOS DE EJEMPLO (MOCK)
========================================================= */

const DB_SIMULADA = {
  1: {
    poblacion: 31,
    incremento: "+3 vs. mes ant.",
    riesgo: { nivel: "Bajo", score: 48 },
    distribucion: [
      ["Bajo", "65%"],
      ["Medio", "28%"],
      ["Alto", "7%"],
    ],
    chart: {
      meses: ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep"],
      puntaje: [55, 58, 60, 57, 62, 59, 61, 63, 60],
      umbral: [70, 70, 70, 70, 70, 70, 70, 70, 70],
    },
    respondientes: [
      { id: 101, nombre: "Laura Gómez", fecha: "2026-09-02", puntaje: 61, nivelRiesgo: "Medio" },
      { id: 102, nombre: "Carlos Pérez", fecha: "2026-09-03", puntaje: 45, nivelRiesgo: "Bajo" },
      { id: 103, nombre: "Andrea Ruiz", fecha: "2026-09-05", puntaje: 78, nivelRiesgo: "Alto" },
      { id: 104, nombre: "Julián Torres", fecha: "2026-09-06", puntaje: 52, nivelRiesgo: "Bajo" },
    ],
  },
  2: {
    poblacion: 31,
    incremento: "+4 vs. mes ant.",
    riesgo: { nivel: "Medio", score: 62 },
    distribucion: [
      ["Bajo", "58%"],
      ["Medio", "33%"],
      ["Alto", "9%"],
    ],
    chart: {
      meses: ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep"],
      puntaje: [50, 53, 57, 60, 58, 63, 65, 62, 64],
      umbral: [70, 70, 70, 70, 70, 70, 70, 70, 70],
    },
    respondientes: [
      { id: 201, nombre: "Mariana López", fecha: "2026-09-01", puntaje: 64, nivelRiesgo: "Medio" },
      { id: 202, nombre: "Santiago Rojas", fecha: "2026-09-04", puntaje: 80, nivelRiesgo: "Alto" },
      { id: 203, nombre: "Valentina Díaz", fecha: "2026-09-07", puntaje: 40, nivelRiesgo: "Bajo" },
      { id: 204, nombre: "Esteban Cárdenas", fecha: "2026-09-08", puntaje: 58, nivelRiesgo: "Medio" },
      { id: 205, nombre: "Paula Herrera", fecha: "2026-09-10", puntaje: 62, nivelRiesgo: "Medio" },
    ],
  },
  3: {
    poblacion: 123,
    incremento: "+12 vs. mes ant.",
    riesgo: { nivel: "Medio", score: 55 },
    distribucion: [
      ["Bajo", "50%"],
      ["Medio", "37%"],
      ["Alto", "13%"],
    ],
    chart: {
      meses: ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep"],
      puntaje: [48, 50, 52, 55, 53, 56, 58, 57, 59],
      umbral: [70, 70, 70, 70, 70, 70, 70, 70, 70],
    },
    respondientes: [
      { id: 301, nombre: "Diego Martínez", fecha: "2026-09-02", puntaje: 59, nivelRiesgo: "Medio" },
      { id: 302, nombre: "Camila Suárez", fecha: "2026-09-03", puntaje: 71, nivelRiesgo: "Alto" },
      { id: 303, nombre: "Felipe Ortiz", fecha: "2026-09-05", puntaje: 38, nivelRiesgo: "Bajo" },
    ],
  },
  4: {
    poblacion: 31,
    incremento: "+1 vs. mes ant.",
    riesgo: { nivel: "Bajo", score: 20 },
    distribucion: [
      ["Bajo", "90%"],
      ["Medio", "8%"],
      ["Alto", "2%"],
    ],
    chart: {
      meses: ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep"],
      puntaje: [15, 16, 18, 17, 19, 18, 20, 19, 20],
      umbral: [70, 70, 70, 70, 70, 70, 70, 70, 70],
    },
    respondientes: [
      { id: 401, nombre: "Isabella Moreno", fecha: "2026-09-01", puntaje: 19, nivelRiesgo: "Bajo" },
      { id: 402, nombre: "Nicolás Vargas", fecha: "2026-09-06", puntaje: 22, nivelRiesgo: "Bajo" },
    ],
  },
};

/**
 * Simula la llamada a la base de datos / API.
 * Reemplaza el cuerpo por tu fetch real cuando tengas el backend:
 *
 *   const res = await fetch(`/api/categorias/${categoriaId}/resultados`);
 *   if (!res.ok) throw new Error("Error al cargar la categoría");
 *   return await res.json();
 */
function obtenerDatosCategoria(categoriaId) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const datos = DB_SIMULADA[categoriaId];
      if (datos) {
        resolve(datos);
      } else {
        reject(new Error("No hay datos para esta categoría"));
      }
    }, 350);
  });
}

export default function Dashboard() {

  const [mostrarModal, setMostrarModal] = useState(false);
  const [categoriaActivaId, setCategoriaActivaId] = useState(2);
  const [datosCategoria, setDatosCategoria] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState(null);

  const navigate = useNavigate();

  const categoriaActiva = CATEGORIAS.find((c) => c.id === categoriaActivaId);

  const cargarCategoria = useCallback((id) => {
    setCargando(true);
    setError(null);

    obtenerDatosCategoria(id)
      .then((datos) => {
        setDatosCategoria(datos);
      })
      .catch((err) => {
        setError(err.message);
        setDatosCategoria(null);
      })
      .finally(() => {
        setCargando(false);
      });
  }, []);

  useEffect(() => {
    cargarCategoria(categoriaActivaId);
  }, [categoriaActivaId, cargarCategoria]);

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

          <button className="menu-item active" type="button" onClick={() => navigate("/cuestionarios")}>
            <span>▣</span>
            Cuestionario
          </button>

          <button className="menu-item" type="button" onClick={() => navigate("/resultados")}>
            <span>☑</span>
            Mis resultados
          </button>

          <button className="menu-item" type="button" onClick={() => navigate("/ayuda")}>
            <span>?</span>
            Ayuda
          </button>

          <button className="menu-item" type="button" onClick={() => navigate("/")}>
            <span>X</span>
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
            <h1>Bienvenido</h1>
            <p>Tu bienestar también es parte del trabajo</p>
          </div>

          <button className="profile" type="button" onClick={() => navigate("/perfil")} aria-label="Ir al perfil de usuario">
            <img
            src="/icono.png"
            alt="Magnus"
            style={{ height: 60, marginRight: "auto" }}
          />
          </button>

        </header>

        <section className="welcome-card">

          <div className="welcome-icon">ⓘ</div>

          <div className="welcome-text">
            <h2>Batería Psicológica</h2>
            <p>
              Este cuestionario nos permite conocer aspectos
              de tu estado emocional, nivel de estrés y
              bienestar laboral.
            </p>
          </div>

          <button className="welcome-button" type="button" onClick={() => setMostrarModal(true)} aria-label="Seleccionar cuestionario">
            ✓
          </button>

        </section>

        <div className="category-tabs">

          {CATEGORIAS.map((categoria) => (
            <button
              key={categoria.id}
              type="button"
              className={categoria.id === categoriaActivaId ? "selected" : ""}
              onClick={() => setCategoriaActivaId(categoria.id)}
              aria-pressed={categoria.id === categoriaActivaId}
            >
              {categoria.nombre}
              <small>{categoria.totalPreguntas}</small>
            </button>
          ))}

        </div>

        {error && (
          <p className="error-text">
            No se pudieron cargar los datos de "{categoriaActiva?.nombre}": {error}
          </p>
        )}

        <section className="dashboard-grid">

          <div className="chart-card">

            <div className="card-title">

              <div>
                <h3>Tendencia — {categoriaActiva?.nombre}</h3>
                <p>Puntaje promedio por corte de evaluación</p>
              </div>

              <div className="legend">
                <span>
                  <i className="dot green"></i>
                  Puntaje
                </span>
                <span>
                  <i className="dot orange"></i>
                  Umbral riesgo
                </span>
              </div>

            </div>

            <div className="chart">
              {cargando || !datosCategoria ? (
                <p className="chart-loading">Cargando gráfica...</p>
              ) : (
                <TendenciaChart
                  key={categoriaActivaId}
                  meses={datosCategoria.chart.meses}
                  puntaje={datosCategoria.chart.puntaje}
                  umbral={datosCategoria.chart.umbral}
                />
              )}
            </div>

          </div>

          <div className="side-card population-card">
            <p>Población estudiada</p>
            <strong>{cargando ? "…" : datosCategoria?.poblacion ?? "—"}</strong>
            <span className="increase">
              {cargando ? "" : datosCategoria?.incremento}
            </span>
          </div>

          <div className="side-card risk-card">
            <h3>Nivel de riesgo promedio</h3>
            <div className="risk-circle">
              <div>
                <strong>{cargando ? "…" : datosCategoria?.riesgo.nivel}</strong>
                <small>
                  {cargando ? "" : `Score ${datosCategoria?.riesgo.score}/100`}
                </small>
              </div>
            </div>
          </div>

        </section>

        <section className="indicators">

          {CATEGORIAS.map((categoria) => {
            const esActiva = categoria.id === categoriaActivaId;
            const datos = esActiva ? datosCategoria : null;

            return (
              <Indicator
                key={categoria.id}
                title={categoria.nombre}
                subtitle={`${categoria.totalPreguntas} preguntas`}
                active={esActiva}
                values={
                  esActiva && datos
                    ? datos.distribucion
                    : [
                        ["Bajo", "—"],
                        ["Medio", "—"],
                        ["Alto", "—"],
                      ]
                }
                onClick={() => setCategoriaActivaId(categoria.id)}
              />
            );
          })}

        </section>

        {/* =================================================
            PERSONAS QUE HAN RESPONDIDO
        ================================================= */}

        <section className="responders-card">

          <h3>Personas que respondieron — {categoriaActiva?.nombre}</h3>
          <p>
            {cargando
              ? "Cargando..."
              : `${datosCategoria?.respondientes.length ?? 0} persona(s) han completado este cuestionario`}
          </p>

          {cargando && (
            <p className="chart-loading">Cargando personas...</p>
          )}

          {!cargando && datosCategoria && datosCategoria.respondientes.length === 0 && (
            <p className="chart-loading">Todavía nadie ha respondido este cuestionario.</p>
          )}

          {!cargando && datosCategoria && datosCategoria.respondientes.length > 0 && (
            <div className="table-wrap">
              <table className="responders-table">
                <thead>
                  <tr>
                    <th>Nombre</th>
                    <th>Fecha</th>
                    <th>Puntaje</th>
                    <th>Nivel de riesgo</th>
                  </tr>
                </thead>
                <tbody>
                  {datosCategoria.respondientes.map((persona) => (
                    <tr key={persona.id}>
                      <td>{persona.nombre}</td>
                      <td>{persona.fecha}</td>
                      <td>{persona.puntaje}</td>
                      <td>
                        <span className={`risk-badge ${persona.nivelRiesgo.toLowerCase()}`}>
                          {persona.nivelRiesgo}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

        </section>

      </main>

      {mostrarModal && (

        <div className="modal-overlay" onClick={() => setMostrarModal(false)}>

          <div className="questionnaire-modal" onClick={(e) => e.stopPropagation()}>

            <button className="modal-close" type="button" onClick={() => setMostrarModal(false)} aria-label="Cerrar ventana">
              ×
            </button>

            <div className="modal-icon">
              <img
                src="/logo a 2_Mesa de trabajo 1.jpg"
                alt="Magnus"
                style={{ height: 160, marginRight: "auto" }}
              />
            </div>

            <h2>¿Qué cuestionario deseas realizar?</h2>
            <p>
              Selecciona el cuestionario que deseas realizar
              para continuar con la evaluación.
            </p>

            <div className="questionnaire-options">

              <button type="button" onClick={() => navigate("/cuestionarios")}>
                <strong>Cuestionario de Estrés</strong>
                <span>Evaluación de síntomas relacionados con estrés.</span>
              </button>

              <button type="button" onClick={() => navigate("/cuestionarios")}>
                <strong>Evaluación Extralaboral</strong>
                <span>Evaluación de factores externos al trabajo.</span>
              </button>

              <button type="button" onClick={() => navigate("/cuestionarios")}>
                <strong>Evaluación Intralaboral</strong>
                <span>Evaluación de las condiciones dentro del entorno laboral.</span>
              </button>

            </div>

            <button className="modal-main-button" type="button" onClick={() => navigate("/cuestionarios")}>
              Ir a cuestionarios
            </button>

          </div>
        </div>
      )}

    </div>
  );
}

/* =========================================================
   GRÁFICA DE TENDENCIA
========================================================= */

function TendenciaChart({ meses, puntaje, umbral }) {
  const width = 700;
  const height = 220;
  const paddingX = 30;
  const paddingY = 20;

  const todos = [...puntaje, ...umbral];
  const max = Math.max(...todos) + 10;
  const min = Math.min(0, Math.min(...todos) - 10);

  const escalarX = (i) =>
    paddingX + (i * (width - paddingX * 2)) / (meses.length - 1);

  const escalarY = (valor) =>
    height - paddingY - ((valor - min) * (height - paddingY * 2)) / (max - min);

  const puntosALinea = (valores) =>
    valores.map((v, i) => `${escalarX(i)},${escalarY(v)}`).join(" ");

  return (
    <svg viewBox={`0 0 ${width} ${height + 24}`} width="100%" role="img" aria-label="Gráfica de tendencia">

      <polyline points={puntosALinea(umbral)} fill="none" stroke="#ef8267" strokeWidth="2" strokeDasharray="6 4" />

      <polyline points={puntosALinea(puntaje)} fill="none" stroke="#2e7869" strokeWidth="3" />

      {puntaje.map((v, i) => (
        <circle key={i} cx={escalarX(i)} cy={escalarY(v)} r="3.5" fill="#2e7869" />
      ))}

      {meses.map((mes, i) => (
        <text key={mes} x={escalarX(i)} y={height + 16} fontSize="10" textAnchor="middle" fill="#aaa59c">
          {mes}
        </text>
      ))}

    </svg>
  );
}

/* =========================================================
   COMPONENTE INDICADOR
========================================================= */

function Indicator({ title, subtitle, values, active, onClick }) {

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

        {values.map(([name, percentage]) => (
          <div className="indicator-row" key={name}>

            <span>{name}</span>

            <div className="progress">
              <div
                className={`progress-fill ${name.toLowerCase()}`}
                style={{ width: percentage === "—" ? "0%" : percentage }}
              ></div>
            </div>

            <small>{percentage}</small>

          </div>
        ))}

      </div>

    </div>

  );
}