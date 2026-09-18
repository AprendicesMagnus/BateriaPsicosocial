import { useLocation } from "react-router-dom";
import AppTopbar from "../components/AppTopbar";
import "../styles/app-shell.css";
import "../styles/reportes.css";

// =================================================
// Datos de ejemplo — se usan solo mientras no exista
// el módulo real que entregue reportes generados.
// =================================================
const REPORTES_EJEMPLO = [
  {
    id: "general",
    titulo: "Reporte general",
    descripcion: "Resumen consolidado de todos los instrumentos · 86 trabajadores evaluados",
    color: "#2D6CDF",
    estado: "listo",
  },
  {
    id: "intralaboral-a",
    titulo: "Cuestionario intralaboral · Forma A",
    descripcion: "Jefes, profesionales y técnicos · 34 respuestas registradas",
    color: "#1F9D55",
    estado: "listo",
  },
  {
    id: "intralaboral-b",
    titulo: "Cuestionario intralaboral · Forma B",
    descripcion: "Auxiliares y operarios · 52 respuestas registradas",
    color: "#6C4FD4",
    estado: "listo",
  },
  {
    id: "extralaboral",
    titulo: "Cuestionario extralaboral",
    descripcion: "Aplicado a todos los niveles del cargo · 86 respuestas registradas",
    color: "#DD8F13",
    estado: "listo",
  },
  {
    id: "ficha-general",
    titulo: "Ficha de datos generales",
    descripcion: "Información sociodemográfica y ocupacional · 86 registros",
    color: "#6B7290",
    estado: "listo",
  },
  {
    id: "analisis-individual",
    titulo: "Guía de análisis individual",
    descripcion: "Casos de riesgo alto o muy alto · 7 casos identificados",
    color: "#D64545",
    estado: "restringido",
  },
];

function IconoDocumento({ color }) {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
      <path
        d="M6 3h9l5 5v13a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z"
        fill={color}
        opacity="0.15"
      />
      <path
        d="M6 3h9l5 5v13a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z"
        stroke={color}
        strokeWidth="1.6"
        fill="none"
      />
      <path d="M15 3v5h5" stroke={color} strokeWidth="1.6" fill="none" />
    </svg>
  );
}

function IconoCandado() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none">
      <rect x="5" y="11" width="14" height="9" rx="2" fill="currentColor" />
      <path d="M8 11V7a4 4 0 0 1 8 0v4" stroke="currentColor" strokeWidth="2" fill="none" />
    </svg>
  );
}

function IconoDescargar() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" style={{ marginRight: 6 }}>
      <path d="M12 3v12m0 0-4-4m4 4 4-4" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M5 19h14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

export default function Reportes() {
  const location = useLocation();

  // =================================================
  // Datos reales de la empresa/batería y sus reportes.
  // Deben llegar navegando desde el flujo real, por ejemplo:
  // navigate("/reportes", { state: { empresaNombre, sector, bateriaNombre, rangoFechas, reportes } })
  // Mientras ese módulo no exista, se usan valores de ejemplo.
  // Si "reportes" llega como un arreglo vacío ([]), se muestra el estado vacío.
  // =================================================
  const {
    empresaNombre = "Agrocampo S.A.S.",
    sector = "Agropecuario",
    bateriaNombre = "Batería de riesgo psicosocial",
    rangoFechas = "aplicada del 12 al 26 de agosto de 2026",
    reportes = REPORTES_EJEMPLO,
  } = location.state || {};

  function handleDescargar(reporte) {
    if (reporte.estado === "restringido") return;
    // TODO: conectar con el endpoint real que genera/descarga el archivo del reporte.
    console.log("Descargando reporte:", reporte.id);
  }

  return (
    <div className="app-shell-page">
      <AppTopbar />

      {/* =================================================
          FONDO OSCURO + CONTENIDO
          ================================================= */}
      <main className="app-hero">
        <div className="app-decor app-decor--1" />
        <div className="app-decor app-decor--2" />
        <div className="app-decor app-decor--3" />

        <div className="app-content">
          <nav className="app-breadcrumb">
            Reportes <span>›</span> {empresaNombre}
          </nav>

          <div className="app-title-row">
            <h1 className="app-title">{empresaNombre}</h1>
            <span className="reportes-tag">{sector}</span>
          </div>

          <p className="app-subtitle">
            {bateriaNombre} · {rangoFechas}
          </p>

          <p className="reportes-legal-note">
            Desglosados por instrumento de la batería, según la Resolución 2764 de 2022
          </p>

          <div className="app-card reportes-card">
            {reportes.length === 0 ? (
              <div className="reportes-empty">
                <IconoDocumento color="#9AA1BD" />
                <p>
                  Todavía no hay reportes disponibles para esta batería.
                  <br />
                  Aparecerán aquí automáticamente cuando la aplicación esté completa.
                </p>
              </div>
            ) : (
              reportes.map((reporte) => (
                <div className="reportes-item" key={reporte.id}>
                  <div className="reportes-item-icon" style={{ background: `${reporte.color}22` }}>
                    <IconoDocumento color={reporte.color} />
                  </div>

                  <div className="reportes-item-info">
                    <span className="reportes-item-title">{reporte.titulo}</span>
                    <span className="reportes-item-desc">{reporte.descripcion}</span>
                  </div>

                  <span
                    className={`reportes-status ${
                      reporte.estado === "listo" ? "reportes-status--listo" : "reportes-status--restringido"
                    }`}
                  >
                    {reporte.estado === "restringido" && <IconoCandado />}
                    {reporte.estado === "listo" ? "Listo" : "Acceso restringido"}
                  </span>

                  <button
                    type="button"
                    className={`reportes-download-btn ${
                      reporte.estado === "restringido" ? "reportes-download-btn--disabled" : ""
                    }`}
                    onClick={() => handleDescargar(reporte)}
                    disabled={reporte.estado === "restringido"}
                  >
                    <IconoDescargar /> Descargar
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      </main>
    </div>
  );
}