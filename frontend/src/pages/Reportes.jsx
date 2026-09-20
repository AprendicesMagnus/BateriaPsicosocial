import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import AppTopbar from "../components/AppTopbar";
import { useAuth } from "../context/AuthContext";
import { fetchReportes } from "../api/reportes";
import { generarInformeAgrupado, descargarInforme } from "../api/informes";
import "../styles/app-shell.css";
import "../styles/Reportes.css";

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
  const { token, usuario } = useAuth();
  const location = useLocation();

  const [reportes, setReportes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [descargandoId, setDescargandoId] = useState(null);

  const {
    empresaNombre = usuario?.organizacionNombre || "Organización",
    sector = usuario?.sector || "General",
    bateriaNombre = "Batería de riesgo psicosocial",
    rangoFechas = "vigente 2026",
  } = location.state || {};

  useEffect(() => {
    if (token) {
      cargarReportes();
    }
  }, [token]);

  async function cargarReportes() {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchReportes(token);
      setReportes(data || []);
    } catch (err) {
      setError(err.message || "Error al cargar la lista de reportes.");
    } finally {
      setLoading(false);
    }
  }

  async function handleDescargar(reporte) {
    if (reporte.estado === "restringido") return;
    setDescargandoId(reporte.id);
    setError(null);
    try {
      if (!reporte.evaluacionId) {
        throw new Error("No hay una evaluación registrada para esta área.");
      }
      const resInforme = await generarInformeAgrupado(
        token,
        reporte.evaluacionId,
        reporte.areaId,
        "PDF"
      );
      await descargarInforme(token, resInforme.id);
    } catch (err) {
      setError(`Error al descargar informe de ${reporte.areaNombre}: ${err.message}`);
    } finally {
      setDescargandoId(null);
    }
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
            Desglosados por área de la organización, según la Resolución 2764 de 2022 (Anonimizado mín. 5 participantes)
          </p>

          {error && (
            <div style={{ padding: "12px 16px", background: "#FEF2F2", color: "#991B1B", borderRadius: "8px", marginBottom: "16px" }}>
              ⚠️ {error}
            </div>
          )}

          <div className="app-card reportes-card">
            {loading ? (
              <div style={{ padding: "32px", textAlign: "center", color: "#64748B" }}>
                Cargando reportes por área...
              </div>
            ) : reportes.length === 0 ? (
              <div className="reportes-empty">
                <IconoDocumento color="#9AA1BD" />
                <p>
                  Todavía no hay áreas registradas o reportes disponibles para esta organización.
                  <br />
                  Aparecerán aquí automáticamente cuando existan áreas y evaluaciones asignadas.
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
                      reporte.estado === "restringido" || descargandoId === reporte.id ? "reportes-download-btn--disabled" : ""
                    }`}
                    onClick={() => handleDescargar(reporte)}
                    disabled={reporte.estado === "restringido" || descargandoId === reporte.id}
                  >
                    <IconoDescargar /> {descargandoId === reporte.id ? "Generando..." : "Descargar"}
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