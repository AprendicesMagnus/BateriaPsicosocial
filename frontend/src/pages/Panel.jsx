import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Logo from "../components/Logo";
import { useAuth } from "../context/AuthContext";
import { fetchIndicadores } from "../api/indicadores";
import { generarInformeAgrupado, generarInformeIndividual, descargarInforme } from "../api/informes";
import { fetchAnalisisPredictivo } from "../api/prediccion";
import ListaEvaluacionesTrabajador from "../components/ListaEvaluacionesTrabajador";
import CuestionarioTrabajador from "../components/CuestionarioTrabajador";
import HistoricoComparativo from "../components/HistoricoComparativo";
import PlanDeAccion from "../components/PlanDeAccion";
import { uuidValido } from "../utils/validaciones";

const ROL_LABEL = {
  SUPER_ADMINISTRADOR: "Super Administrador",
  ADMINISTRADOR: "Administrador",
  JEFE: "Jefe",
  EVALUADOR_SST: "Psicologo",
};

export default function Panel() {
  const { usuario, token, cerrarSesion } = useAuth();
  const navigate = useNavigate();

  const [indicadores, setIndicadores] = useState(null);
  const [loadingIndicadores, setLoadingIndicadores] = useState(false);
  const [errorIndicadores, setErrorIndicadores] = useState(null);

  const [informeId, setInformeId] = useState("");
  const [evaluacionIdInput, setEvaluacionIdInput] = useState("");
  const [participanteIdInput, setParticipanteIdInput] = useState("");
  const [mensajeInforme, setMensajeInforme] = useState(null);
  const [errorInforme, setErrorInforme] = useState(null);
  const [generando, setGenerando] = useState(false);

  const [prediccionData, setPrediccionData] = useState(null);
  const [loadingPrediccion, setLoadingPrediccion] = useState(false);

  const [evaluacionSeleccionadaId, setEvaluacionSeleccionadaId] = useState(null);

  useEffect(() => {
    if (token && usuario && usuario.rol !== "TRABAJADOR") {
      cargarIndicadores();
    }
  }, [token, usuario]);

  async function cargarIndicadores() {
    setLoadingIndicadores(true);
    setErrorIndicadores(null);
    try {
      const data = await fetchIndicadores(token);
      setIndicadores(data);
    } catch (err) {
      setErrorIndicadores(err.message);
    } finally {
      setLoadingIndicadores(false);
    }
  }

  async function handleGenerarAgrupado(formato = "PDF") {
    if (!uuidValido(evaluacionIdInput.trim())) {
      setErrorInforme("Ingresa un identificador válido (formato UUID).");
      return;
    }
    setGenerando(true);
    setErrorInforme(null);
    setMensajeInforme(null);
    try {
      const res = await generarInformeAgrupado(token, evaluacionIdInput.trim(), null, formato);
      setInformeId(res.id);
      setMensajeInforme(`Informe agrupado (${formato}) generado con éxito. ID: ${res.id}`);
    } catch (err) {
      setErrorInforme(err.message);
    } finally {
      setGenerando(false);
    }
  }

  async function handleGenerarIndividual() {
    if (!uuidValido(evaluacionIdInput.trim()) || !uuidValido(participanteIdInput.trim())) {
      setErrorInforme("Ingresa un identificador válido (formato UUID).");
      return;
    }
    setGenerando(true);
    setErrorInforme(null);
    setMensajeInforme(null);
    try {
      const res = await generarInformeIndividual(token, evaluacionIdInput.trim(), participanteIdInput.trim());
      setInformeId(res.id);
      setMensajeInforme(`Informe individual PDF generado con éxito. ID: ${res.id}`);
    } catch (err) {
      setErrorInforme(err.message);
    } finally {
      setGenerando(false);
    }
  }

  async function handleDescargar() {
    if (!uuidValido(informeId.trim())) {
      setErrorInforme("Ingresa un identificador válido (formato UUID).");
      return;
    }
    setErrorInforme(null);
    try {
      await descargarInforme(token, informeId.trim());
      setMensajeInforme("Descarga iniciada exitosamente.");
    } catch (err) {
      setErrorInforme(err.message);
    }
  }

  async function handleCargarPrediccion() {
    if (!uuidValido(evaluacionIdInput.trim())) {
      setErrorInforme("Ingresa un identificador válido (formato UUID).");
      return;
    }
    setLoadingPrediccion(true);
    try {
      const data = await fetchAnalisisPredictivo(token, evaluacionIdInput.trim());
      setPrediccionData(data);
    } catch (err) {
      setErrorInforme(`Error predictivo: ${err.message}`);
    } finally {
      setLoadingPrediccion(false);
    }
  }

  function handleLogout() {
    cerrarSesion();
    navigate("/");
  }

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg-100)" }}>
      <header
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "18px 32px",
          background: "var(--white)",
          borderBottom: "1px solid var(--line-200)",
        }}
      >
        <Logo />
        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          <span style={{ fontSize: "14px", color: "var(--ink-500)" }}>
            {usuario?.nombre} ({ROL_LABEL[usuario?.rol] || usuario?.rol})
          </span>
          <button className="btn-secondary" onClick={handleLogout}>
            Cerrar sesión
          </button>
        </div>
      </header>

      <main style={{ maxWidth: 1000, margin: "40px auto", padding: "0 24px" }}>
        <h1 style={{ color: "var(--ink-900)", marginBottom: "8px" }}>
          Panel de Control BRP 👋
        </h1>
        <p style={{ color: "var(--ink-500)", marginBottom: "32px" }}>
          {usuario?.rol === "TRABAJADOR"
            ? "Gestión de Evaluaciones de Riesgo Psicosocial Asignadas y Consulta de Resultados."
            : "Gestión de la Batería de Riesgo Psicosocial, Indicadores (RF08), Histórico Comparativo, Informes y Análisis Predictivo IA."}
        </p>

        {/* VISTA TRABAJADOR: CUESTIONARIO ACTIVO O LISTA DE EVALUACIONES */}
        {usuario?.rol === "TRABAJADOR" ? (
          evaluacionSeleccionadaId ? (
            <CuestionarioTrabajador
              evaluacionId={evaluacionSeleccionadaId}
              token={token}
              onVolver={() => setEvaluacionSeleccionadaId(null)}
            />
          ) : (
            <section style={{ marginBottom: "32px" }}>
              <h2 style={{ fontSize: "20px", color: "#1E293B", marginBottom: "16px" }}>
                📋 Mis Evaluaciones Asignadas
              </h2>
              <ListaEvaluacionesTrabajador
                token={token}
                onSeleccionarEvaluacion={(id) => setEvaluacionSeleccionadaId(id)}
              />
            </section>
          )
        ) : null}

        {/* METRICAS E INDICADORES (RF08) - SOLO ADMIN Y EVALUADOR */}
        {usuario?.rol !== "TRABAJADOR" && (
          <section style={{ background: "white", padding: "24px", borderRadius: "12px", border: "1px solid #E2E8F0", marginBottom: "32px" }}>
            <h2 style={{ fontSize: "20px", color: "#1E293B", marginBottom: "16px" }}>
              📊 Indicadores y Métricas Generales (RF08)
            </h2>

            {loadingIndicadores && <p>Cargando indicadores...</p>}
            {errorIndicadores && <p style={{ color: "red" }}>{errorIndicadores}</p>}

            {indicadores && (
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "16px" }}>
                <div style={{ background: "#F8FAFC", padding: "16px", borderRadius: "8px", border: "1px solid #E2E8F0" }}>
                  <div style={{ fontSize: "12px", color: "#64748B" }}>Organizaciones</div>
                  <div style={{ fontSize: "28px", fontWeight: "bold", color: "#1E3A8A" }}>{indicadores.totalOrganizaciones}</div>
                </div>

                <div style={{ background: "#F8FAFC", padding: "16px", borderRadius: "8px", border: "1px solid #E2E8F0" }}>
                  <div style={{ fontSize: "12px", color: "#64748B" }}>Evaluaciones Totales</div>
                  <div style={{ fontSize: "28px", fontWeight: "bold", color: "#1E3A8A" }}>{indicadores.totalEvaluaciones}</div>
                  <div style={{ fontSize: "11px", color: "#475569" }}>
                    En Curso: {indicadores.evaluacionesPorEstado.EN_CURSO} | Finalizadas: {indicadores.evaluacionesPorEstado.FINALIZADA}
                  </div>
                </div>

                <div style={{ background: "#F8FAFC", padding: "16px", borderRadius: "8px", border: "1px solid #E2E8F0" }}>
                  <div style={{ fontSize: "12px", color: "#64748B" }}>Tasa de Participación</div>
                  <div style={{ fontSize: "28px", fontWeight: "bold", color: "#059669" }}>{indicadores.participacion.tasaPorcentaje}%</div>
                  <div style={{ fontSize: "11px", color: "#475569" }}>
                    Completados: {indicadores.participacion.totalCompletados} / {indicadores.participacion.totalAsignados}
                  </div>
                </div>
              </div>
            )}
          </section>
        )}

        {/* HISTORICO COMPARATIVO ENTRE EVALUACIONES - SOLO ADMIN Y EVALUADOR */}
        {usuario?.rol !== "TRABAJADOR" && (
          <section style={{ marginBottom: "32px" }}>
            <HistoricoComparativo token={token} />
            <PlanDeAccion token={token} />
          </section>
        )}

        {/* MODULO DE INFORMES */}
        {(!evaluacionSeleccionadaId || usuario?.rol !== "TRABAJADOR") && (
          <section style={{ background: "white", padding: "24px", borderRadius: "12px", border: "1px solid #E2E8F0", marginBottom: "32px" }}>
            <h2 style={{ fontSize: "20px", color: "#1E293B", marginBottom: "16px" }}>
              📑 Generación y Descarga de Informes (PDF / Excel)
            </h2>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginBottom: "16px" }}>
              <div>
                <label style={{ display: "block", fontSize: "13px", fontWeight: "600", marginBottom: "4px" }}>ID Evaluación</label>
                <input
                  type="text"
                  maxLength={36}
                  placeholder="UUID de la Evaluación"
                  value={evaluacionIdInput}
                  onChange={(e) => setEvaluacionIdInput(e.target.value)}
                  style={{ width: "100%", padding: "8px 12px", borderRadius: "6px", border: "1px solid #CBD5E1" }}
                />
              </div>
              <div>
                <label style={{ display: "block", fontSize: "13px", fontWeight: "600", marginBottom: "4px" }}>ID Participante (para informe individual)</label>
                <input
                  type="text"
                  maxLength={36}
                  placeholder="UUID del Participante"
                  value={participanteIdInput}
                  onChange={(e) => setParticipanteIdInput(e.target.value)}
                  style={{ width: "100%", padding: "8px 12px", borderRadius: "6px", border: "1px solid #CBD5E1" }}
                />
              </div>
            </div>

            <div style={{ display: "flex", gap: "12px", flexWrap: "wrap", marginBottom: "16px" }}>
              {usuario?.rol !== "TRABAJADOR" && (
                <>
                  <button className="btn-secondary" onClick={() => handleGenerarAgrupado("PDF")} disabled={generando}>
                    Generar Agrupado (PDF)
                  </button>
                  <button className="btn-secondary" onClick={() => handleGenerarAgrupado("EXCEL")} disabled={generando}>
                    Generar Agrupado (Excel)
                  </button>
                </>
              )}
              <button className="btn-secondary" onClick={handleGenerarIndividual} disabled={generando}>
                Generar Individual (PDF)
              </button>
              {usuario?.rol !== "TRABAJADOR" && (
                <button className="btn-secondary" onClick={handleCargarPrediccion} disabled={loadingPrediccion}>
                  Analizar con IA (K-Means)
                </button>
              )}
            </div>

            <div style={{ marginTop: "16px", paddingTop: "16px", borderTop: "1px solid #E2E8F0" }}>
              <label style={{ display: "block", fontSize: "13px", fontWeight: "600", marginBottom: "4px" }}>Descargar Informe por ID</label>
              <div style={{ display: "flex", gap: "12px" }}>
                <input
                  type="text"
                  maxLength={36}
                  placeholder="ID del Informe a descargar"
                  value={informeId}
                  onChange={(e) => setInformeId(e.target.value)}
                  style={{ flex: 1, padding: "8px 12px", borderRadius: "6px", border: "1px solid #CBD5E1" }}
                />
                <button className="btn-primary" onClick={handleDescargar}>
                  Descargar Archivo
                </button>
              </div>
            </div>

            {mensajeInforme && (
              <div style={{ marginTop: "16px", padding: "12px", background: "#ECFDF5", color: "#065F46", borderRadius: "6px", fontSize: "14px" }}>
                {mensajeInforme}
              </div>
            )}

            {errorInforme && (
              <div style={{ marginTop: "16px", padding: "12px", background: "#FEF2F2", color: "#991B1B", borderRadius: "6px", fontSize: "14px" }}>
                ⚠️ <strong>Error:</strong> {errorInforme}
              </div>
            )}
          </section>
        )}

        {/* MODULO PREDICTIVO (IA) */}
        {prediccionData && usuario?.rol !== "TRABAJADOR" && (
          <section style={{ background: "white", padding: "24px", borderRadius: "12px", border: "1px solid #E2E8F0", marginBottom: "32px" }}>
            <h2 style={{ fontSize: "20px", color: "#1E293B", marginBottom: "8px" }}>
              🤖 Análisis Predictivo K-Means (IA)
            </h2>
            <p style={{ fontSize: "13px", color: "#64748B", marginBottom: "16px" }}>
              {prediccionData.notaMetodologica}
            </p>

            <h3 style={{ fontSize: "16px", color: "#334155", marginBottom: "12px" }}>Perfiles Identificados (Clustering K-Means)</h3>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "16px", marginBottom: "20px" }}>
              {prediccionData.perfilesClusterKMeans.map((c) => (
                <div key={c.clusterId} style={{ background: "#F8FAFC", padding: "16px", borderRadius: "8px", border: "1px solid #CBD5E1" }}>
                  <div style={{ fontWeight: "bold", color: "#1E3A8A", fontSize: "15px" }}>{c.etiqueta}</div>
                  <div style={{ fontSize: "12px", color: "#475569", margin: "4px 0 12px 0" }}>
                    Trabajadores en Clúster: <strong>{c.numTrabajadores} ({c.porcentajeGrupo}%)</strong>
                  </div>
                  <div style={{ fontSize: "12px", color: "#334155" }}>
                    {Object.entries(c.promedioPorDimension).map(([dim, val]) => (
                      <div key={dim} style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
                        <span>{dim}:</span>
                        <strong>{val} pts</strong>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            {prediccionData.alertasTempranas.length > 0 && (
              <div>
                <h3 style={{ fontSize: "16px", color: "#991B1B", marginBottom: "8px" }}>🚨 Alertas Tempranas Proyectadas</h3>
                {prediccionData.alertasTempranas.map((a, i) => (
                  <div key={i} style={{ background: "#FEF2F2", borderLeft: "4px solid #EF4444", padding: "10px 14px", marginBottom: "8px", borderRadius: "4px", fontSize: "13px", color: "#7F1D1D" }}>
                    <strong>[{a.nivelAlerta}] {a.dimension}:</strong> {a.mensaje}
                  </div>
                ))}
              </div>
            )}
          </section>
        )}
      </main>
    </div>
  );
}
