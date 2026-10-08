import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import AppTopbar from "../components/AppTopbar";
import BotonRegresar from "../components/BotonRegresar";
import { useAuth } from "../context/AuthContext";
import { fetchReportes, fetchEncuestasRealizadas } from "../api/reportes";
import { generarInformeAgrupado, descargarInforme } from "../api/informes";
import { fetchEnlaces, crearEnlace, eliminarEnlace } from "../api/enlaces";
import { ESTADOS_ENCUESTA, NIVELES, NOMBRES_INSTRUMENTO, formatearFecha } from "../utils/encuestas";
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

// Roles que pueden crear enlaces para pacientes (EVALUADOR_SST se muestra como "Psicólogo")
const ROLES_ENLACES = ["EVALUADOR_SST", "SUPER_ADMINISTRADOR"];
// Resultados individuales (confidenciales): solo Psicologo y Super Administrador.
const ROLES_ENCUESTAS = ["EVALUADOR_SST", "SUPER_ADMINISTRADOR"];
// Jefe y Administrador ven las empresas que crearon; el Jefe solo consulta (no descarga informes).
const ROLES_POR_CREADOR = ["JEFE", "ADMINISTRADOR"];

// URL completa que el psicólogo comparte con el paciente
function urlEnlace(token) {
  return `${window.location.origin}/responder/${token}`;
}

export default function Reportes() {
  const { token, usuario } = useAuth();
  const location = useLocation();

  const [reportes, setReportes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [descargandoId, setDescargandoId] = useState(null);

  // Estado de la sección "Encuestas realizadas" (independiente de los reportes por área,
  // para que un error en una sección no oculte la otra)
  const [encuestas, setEncuestas] = useState([]);
  const [cargandoEncuestas, setCargandoEncuestas] = useState(true);
  const [errorEncuestas, setErrorEncuestas] = useState(null);
  // participanteId de la encuesta con el detalle abierto (solo una a la vez)
  const [encuestaAbierta, setEncuestaAbierta] = useState(null);

  // Sección "Enlaces para pacientes" (solo psicólogo / super administrador)
  const puedeCrearEnlaces = ROLES_ENLACES.includes(usuario?.rol);
  const puedeVerEncuestas = ROLES_ENCUESTAS.includes(usuario?.rol);
  const puedeDescargar = usuario?.rol !== "JEFE";
  const [enlaces, setEnlaces] = useState([]);
  const [nombreEnlace, setNombreEnlace] = useState("");
  const [creandoEnlace, setCreandoEnlace] = useState(false);
  const [errorEnlaces, setErrorEnlaces] = useState(null);
  // token del enlace recién copiado, para mostrar "¡Copiado!" en su botón
  const [enlaceCopiado, setEnlaceCopiado] = useState(null);
  // evaluacionId del enlace que se está eliminando
  const [eliminandoEnlace, setEliminandoEnlace] = useState(null);

  const {
    empresaNombre = usuario?.organizacionNombre ||
      (ROLES_POR_CREADOR.includes(usuario?.rol) ? "Mis empresas" : "Organización"),
    sector = usuario?.sector || "General",
    bateriaNombre = "Batería de riesgo psicosocial",
    rangoFechas = "vigente 2026",
  } = location.state || {};

  useEffect(() => {
    if (token) {
      cargarReportes();
      if (puedeVerEncuestas) cargarEncuestas();
      else setCargandoEncuestas(false);
    }
  }, [token]);

  // Trae de la BD las encuestas de los trabajadores (GET /api/reportes/encuestas)
  async function cargarEncuestas() {
    setCargandoEncuestas(true);
    setErrorEncuestas(null);
    try {
      const data = await fetchEncuestasRealizadas(token);
      setEncuestas(data || []);
    } catch (err) {
      setErrorEncuestas(err.message || "Error al cargar las encuestas realizadas.");
    } finally {
      setCargandoEncuestas(false);
    }
  }

  useEffect(() => {
    if (token && puedeCrearEnlaces) cargarEnlaces();
  }, [token, puedeCrearEnlaces]);

  async function cargarEnlaces() {
    setErrorEnlaces(null);
    try {
      setEnlaces((await fetchEnlaces(token)) || []);
    } catch (err) {
      setErrorEnlaces(err.message || "Error al cargar los enlaces.");
    }
  }

  async function handleCrearEnlace(e) {
    e.preventDefault();
    if (nombreEnlace.trim().length < 2) {
      setErrorEnlaces("Escribe un nombre para el enlace (mínimo 2 caracteres).");
      return;
    }
    setCreandoEnlace(true);
    setErrorEnlaces(null);
    try {
      const nuevo = await crearEnlace(token, nombreEnlace.trim());
      setEnlaces((prev) => [nuevo, ...prev]);
      setNombreEnlace("");
    } catch (err) {
      setErrorEnlaces(err.message || "Error al crear el enlace.");
    } finally {
      setCreandoEnlace(false);
    }
  }

  async function handleEliminarEnlace(enlace) {
    if (!window.confirm(`¿Eliminar el enlace "${enlace.nombre}"? Si un paciente ya respondió, su encuesta se conserva.`)) {
      return;
    }
    setEliminandoEnlace(enlace.evaluacionId);
    setErrorEnlaces(null);
    try {
      await eliminarEnlace(token, enlace.evaluacionId);
      setEnlaces((prev) => prev.filter((e) => e.evaluacionId !== enlace.evaluacionId));
    } catch (err) {
      setErrorEnlaces(err.message || "Error al eliminar el enlace.");
    } finally {
      setEliminandoEnlace(null);
    }
  }

  async function copiarEnlace(tokenEnlace) {
    try {
      await navigator.clipboard.writeText(urlEnlace(tokenEnlace));
      setEnlaceCopiado(tokenEnlace);
      setTimeout(() => setEnlaceCopiado((actual) => (actual === tokenEnlace ? null : actual)), 2000);
    } catch {
      // Sin permiso de portapapeles: el enlace sigue visible para copiarlo a mano
      setErrorEnlaces("No se pudo copiar automáticamente; selecciona el enlace y cópialo.");
    }
  }

  // Abre o cierra el detalle (instrumentos y resultados) de una encuesta
  function alternarDetalle(participanteId) {
    setEncuestaAbierta((actual) => (actual === participanteId ? null : participanteId));
  }

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
          <BotonRegresar />

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

          {/* =================================================
              ENLACES PARA PACIENTES
              El psicólogo crea un enlace y lo comparte; el paciente responde sin cuenta
              (Ficha de datos + cuestionarios) y aparece abajo en "Encuestas realizadas".
              ================================================= */}
          {puedeCrearEnlaces && (
            <>
              <div className="reportes-section-header" style={{ marginTop: 0 }}>
                <h2 className="reportes-section-title">Enlaces para pacientes</h2>
              </div>
              <p className="reportes-legal-note">
                Comparte el enlace: el paciente responde sin crear cuenta, empezando por la Ficha de datos generales.
                Esta lista se limpia automáticamente cada 4 horas; las encuestas realizadas no se borran.
              </p>

              {errorEnlaces && (
                <div style={{ padding: "12px 16px", background: "#FEF2F2", color: "#991B1B", borderRadius: "8px", marginBottom: "16px" }}>
                  ⚠️ {errorEnlaces}
                </div>
              )}

              <div className="app-card reportes-card" style={{ marginBottom: 40 }}>
                <form className="reportes-item reportes-enlace-form" onSubmit={handleCrearEnlace}>
                  <input
                    type="text"
                    className="reportes-enlace-input"
                    placeholder="Nombre del enlace (p. ej. Pacientes octubre)"
                    maxLength={150}
                    value={nombreEnlace}
                    onChange={(e) => setNombreEnlace(e.target.value)}
                    aria-label="Nombre del enlace"
                  />
                  <button type="submit" className="reportes-download-btn" disabled={creandoEnlace}>
                    {creandoEnlace ? "Creando..." : "Crear enlace"}
                  </button>
                </form>

                {enlaces.map((enlace) => (
                  <div className="reportes-item reportes-enlace" key={enlace.token}>
                    <div className="reportes-item-info">
                      <span className="reportes-item-title">{enlace.nombre}</span>
                      <span className="reportes-item-desc reportes-enlace-url">{urlEnlace(enlace.token)}</span>
                      <span className="reportes-item-desc">
                        {/* Paciente que usó el enlace: su nombre sale de la Ficha de datos */}
                        {!enlace.paciente
                          ? "Esperando que el paciente abra el enlace"
                          : `Paciente: ${enlace.paciente.nombre || "aún no llena la Ficha de datos"} · ${
                              (ESTADOS_ENCUESTA[enlace.paciente.estado] || ESTADOS_ENCUESTA.PENDIENTE).label
                            }`}
                        {" · "}Creado {formatearFecha(enlace.creadoEn)}
                      </span>
                    </div>
                    <span
                      className={`reportes-status ${
                        enlace.estado === "FINALIZADA" ? "reportes-status--restringido" : "reportes-status--listo"
                      }`}
                    >
                      {enlace.estado === "FINALIZADA" ? "Cerrado" : "Activo"}
                    </span>
                    <button type="button" className="reportes-download-btn" onClick={() => copiarEnlace(enlace.token)}>
                      {enlaceCopiado === enlace.token ? "¡Copiado!" : "Copiar enlace"}
                    </button>
                    <button
                      type="button"
                      className="reportes-download-btn reportes-eliminar-btn"
                      onClick={() => handleEliminarEnlace(enlace)}
                      disabled={eliminandoEnlace === enlace.evaluacionId}
                    >
                      {eliminandoEnlace === enlace.evaluacionId ? "Eliminando..." : "Eliminar"}
                    </button>
                  </div>
                ))}
              </div>
            </>
          )}

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

                  {puedeDescargar && (
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
                  )}
                </div>
              ))
            )}
          </div>

          {puedeVerEncuestas && (
          <>
          {/* =================================================
              ENCUESTAS REALIZADAS (datos de la BD)
              Una fila por trabajador y evaluación, con su avance y,
              al abrirla, el estado de cada instrumento y sus niveles de riesgo.
              ================================================= */}
          <div className="reportes-section-header">
            <h2 className="reportes-section-title">Encuestas realizadas</h2>
            <button type="button" className="reportes-refresh-btn" onClick={cargarEncuestas} disabled={cargandoEncuestas}>
              {cargandoEncuestas ? "Actualizando..." : "Actualizar"}
            </button>
          </div>
          <p className="reportes-legal-note">
            Resultados individuales: información confidencial, visible solo para administradores y evaluadores SST.
          </p>

          {errorEncuestas && (
            <div style={{ padding: "12px 16px", background: "#FEF2F2", color: "#991B1B", borderRadius: "8px", marginBottom: "16px" }}>
              ⚠️ {errorEncuestas}
            </div>
          )}

          <div className="app-card reportes-card">
            {cargandoEncuestas && encuestas.length === 0 ? (
              <div style={{ padding: "32px", textAlign: "center", color: "#64748B" }}>
                Cargando encuestas realizadas...
              </div>
            ) : encuestas.length === 0 ? (
              <div className="reportes-empty">
                <IconoDocumento color="#9AA1BD" />
                <p>
                  Todavía no hay encuestas registradas.
                  <br />
                  Aparecerán aquí cuando un trabajador asignado a una evaluación empiece a responder.
                </p>
              </div>
            ) : (
              encuestas.map((encuesta) => {
                const estado = ESTADOS_ENCUESTA[encuesta.estado] || ESTADOS_ENCUESTA.PENDIENTE;
                const abierta = encuestaAbierta === encuesta.participanteId;
                return (
                  <div key={encuesta.participanteId} className="reportes-encuesta">
                    {/* Fila resumen de la encuesta */}
                    <div className="reportes-item">
                      <div className="reportes-item-icon" style={{ background: "#1E3A8A22" }}>
                        <IconoDocumento color="#1E3A8A" />
                      </div>

                      <div className="reportes-item-info">
                        <span className="reportes-item-title">
                          {encuesta.trabajadorNombre}
                          {/* Los pacientes del enlace no tienen correo; su nombre viene de la Ficha */}
                          {encuesta.viaEnlace ? " · Paciente (enlace)" : ` · ${encuesta.trabajadorEmail}`}
                        </span>
                        <span className="reportes-item-desc">
                          {encuesta.evaluacionNombre}
                          {encuesta.organizacionNombre ? ` · ${encuesta.organizacionNombre}` : ""}
                          {" · "}
                          {encuesta.instrumentosCompletados}/{encuesta.instrumentos.length} instrumentos
                          {" · "}
                          {encuesta.fechaFin ? `Finalizó ${formatearFecha(encuesta.fechaFin)}` : `Inició ${formatearFecha(encuesta.fechaInicio)}`}
                        </span>
                      </div>

                      <span className={`reportes-status ${estado.clase}`}>{estado.label}</span>

                      <button
                        type="button"
                        className="reportes-download-btn"
                        onClick={() => alternarDetalle(encuesta.participanteId)}
                        aria-expanded={abierta}
                      >
                        {abierta ? "Ocultar" : "Ver detalle"}
                      </button>
                    </div>

                    {/* Detalle: avance por instrumento y resultados calculados */}
                    {abierta && (
                      <div className="reportes-detalle">
                        <h3 className="reportes-detalle-title">Instrumentos</h3>
                        <div className="reportes-chips">
                          {encuesta.instrumentos.map((inst) => (
                            <span
                              key={inst.codigo}
                              className={`reportes-chip ${inst.estado === "COMPLETADA" ? "reportes-chip--ok" : ""}`}
                              title={inst.nombre}
                            >
                              {inst.estado === "COMPLETADA" ? "✓ " : ""}
                              {NOMBRES_INSTRUMENTO[inst.codigo] || inst.codigo}
                            </span>
                          ))}
                        </div>

                        <h3 className="reportes-detalle-title">Resultados</h3>
                        {encuesta.resultados.length === 0 ? (
                          // Los resultados se calculan solo cuando el trabajador termina toda la batería
                          <p className="reportes-detalle-vacio">
                            Los resultados se calculan cuando el trabajador termina todos los instrumentos.
                          </p>
                        ) : (
                          <table className="reportes-tabla">
                            <thead>
                              <tr>
                                <th>Instrumento</th>
                                <th>Dimensión</th>
                                <th>Puntaje</th>
                                <th>Nivel</th>
                              </tr>
                            </thead>
                            <tbody>
                              {encuesta.resultados.map((r) => {
                                const nivel = NIVELES[r.nivel];
                                return (
                                  <tr key={`${r.instrumento}-${r.dimension}`}>
                                    <td>{NOMBRES_INSTRUMENTO[r.instrumento] || r.instrumento}</td>
                                    <td>{r.dimension}</td>
                                    {/* Puntaje transformado 0-100 */}
                                    <td>{r.puntajeTransformado.toFixed(1)}</td>
                                    <td>
                                      <span
                                        className="reportes-nivel"
                                        style={nivel ? { background: nivel.bg, color: nivel.text } : undefined}
                                      >
                                        {nivel ? nivel.label : r.nivel}
                                      </span>
                                    </td>
                                  </tr>
                                );
                              })}
                            </tbody>
                          </table>
                        )}
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
          </>
          )}
        </div>
      </main>
    </div>
  );
}