import { useEffect, useState } from "react";
import {
  fetchEvaluacionDetalle,
  registrarConsentimiento,
  fetchCuestionario,
  guardarRespuesta,
  finalizarCuestionario,
  fetchResultadosTrabajador,
} from "../api/evaluaciones";

const NIVELES_COLOR = {
  SIN_RIESGO: { bg: "#DEF7EC", text: "#03543F", label: "Sin Riesgo (Verde)" },
  BAJO: { bg: "#E1EFFE", text: "#1E40AF", label: "Riesgo Bajo (Azul)" },
  MEDIO: { bg: "#FEF08A", text: "#713F12", label: "Riesgo Medio (Amarillo)" },
  ALTO: { bg: "#FDBA74", text: "#9A3412", label: "Riesgo Alto (Naranja)" },
  MUY_ALTO: { bg: "#FCA5A5", text: "#991B1B", label: "Riesgo Muy Alto (Rojo)" },
};

const OPCIONES_LIKERT = [
  { valor: 1, etiqueta: "Nunca (1)" },
  { valor: 2, etiqueta: "Casi nunca (2)" },
  { valor: 3, etiqueta: "Algunas veces (3)" },
  { valor: 4, etiqueta: "Casi siempre (4)" },
  { valor: 5, etiqueta: "Siempre (5)" },
];

export default function CuestionarioTrabajador({ evaluacionId, token, onVolver }) {
  const [loading, setLoading] = useState(true);
  const [step, setStep] = useState("cargando"); // cargando | consentimiento | cuestionario | resultados | error
  const [evaluacionInfo, setEvaluacionInfo] = useState(null);
  const [nombreInstrumento, setNombreInstrumento] = useState(null);
  const [preguntas, setPreguntas] = useState([]);
  const [respuestas, setRespuestas] = useState({});
  const [preguntaActualIdx, setPreguntaActualIdx] = useState(0);
  const [guardando, setGuardando] = useState(false);
  const [finalizando, setFinalizando] = useState(false);
  const [resultados, setResultados] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);
  const [consentimientoGuardado, setConsentimientoGuardado] = useState(false);

  useEffect(() => {
    inicializar();
  }, [evaluacionId, token]);

  async function inicializar() {
    setLoading(true);
    setErrorMsg(null);
    try {
      const evalData = await fetchEvaluacionDetalle(token, evaluacionId);
      setEvaluacionInfo(evalData);

      // Try loading questionnaire
      try {
        const questData = await fetchCuestionario(token, evaluacionId);
        setNombreInstrumento(questData.nombre || questData.codigo || null);
        setPreguntas(questData.preguntas || []);
        setPreguntaActualIdx(0);

        // Populate saved answers
        const respMap = {};
        (questData.preguntas || []).forEach((p) => {
          if (p.respuesta !== null && p.respuesta !== undefined) {
            respMap[p.id] = p.respuesta;
          }
        });
        setRespuestas(respMap);
        setConsentimientoGuardado(true);

        if (questData.estado === "COMPLETADA") {
          await cargarResultados();
          setStep("resultados");
        } else {
          setStep("cuestionario");
        }
      } catch (err) {
        // If questionnaire returns 403 because consent is needed:
        if (err.message && err.message.toLowerCase().includes("consentimiento")) {
          setStep("consentimiento");
        } else {
          throw err;
        }
      }
    } catch (err) {
      setErrorMsg(err.message || "Error al cargar la evaluación.");
      setStep("error");
    } finally {
      setLoading(false);
    }
  }

  async function handleAceptarConsentimiento() {
    setLoading(true);
    setErrorMsg(null);
    try {
      await registrarConsentimiento(token, evaluacionId);
      setConsentimientoGuardado(true);
      const questData = await fetchCuestionario(token, evaluacionId);
      setNombreInstrumento(questData.nombre || questData.codigo || null);
      setPreguntas(questData.preguntas || []);
      setPreguntaActualIdx(0);
      setStep("cuestionario");
    } catch (err) {
      setErrorMsg(err.message || "No se pudo registrar el consentimiento.");
    } finally {
      setLoading(false);
    }
  }

  async function handleSeleccionarRespuesta(preguntaId, valor) {
    setRespuestas((prev) => ({ ...prev, [preguntaId]: valor }));
    setGuardando(true);
    try {
      await guardarRespuesta(token, evaluacionId, preguntaId, valor);
    } catch (err) {
      setErrorMsg(`Error guardando respuesta: ${err.message}`);
    } finally {
      setGuardando(false);
    }
  }

  async function handleFinalizar() {
    const respondidasCount = Object.keys(respuestas).length;
    if (respondidasCount < preguntas.length) {
      setErrorMsg(`Debe responder todas las preguntas (${respondidasCount}/${preguntas.length} completadas).`);
      return;
    }

    setFinalizando(true);
    setErrorMsg(null);
    try {
      const res = await finalizarCuestionario(token, evaluacionId);
      if (res.resultados && res.resultados.length > 0) {
        setResultados(res.resultados);
        setStep("resultados");
      } else {
        await inicializar();
      }
    } catch (err) {
      setErrorMsg(err.message || "Error al finalizar la evaluación.");
    } finally {
      setFinalizando(false);
    }
  }

  async function cargarResultados() {
    try {
      const res = await fetchResultadosTrabajador(token, evaluacionId);
      if (res && res.length > 0 && res[0].resultados) {
        setResultados(res[0].resultados);
      }
    } catch (err) {
      // Ignorar si aún no hay resultados
    }
  }

  const pregActual = preguntas[preguntaActualIdx];
  const respondidasCount = Object.keys(respuestas).length;
  const progresoPorcentaje = preguntas.length > 0 ? Math.round((respondidasCount / preguntas.length) * 100) : 0;

  if (loading || step === "cargando") {
    return (
      <div style={{ background: "white", padding: 32, borderRadius: 12, border: "1px solid #E2E8F0", textAlign: "center" }}>
        <p style={{ color: "#64748B" }}>Cargando cuestionario de evaluación...</p>
      </div>
    );
  }

  if (step === "error") {
    return (
      <div style={{ background: "white", padding: 32, borderRadius: 12, border: "1px solid #E2E8F0" }}>
        <h3 style={{ color: "#991B1B", marginBottom: 12 }}>⚠️ No se pudo acceder</h3>
        <p style={{ color: "#475569", marginBottom: 20 }}>{errorMsg}</p>
        <button className="btn-secondary" onClick={onVolver}>
          ← Volver a Mis Evaluaciones
        </button>
      </div>
    );
  }

  if (step === "consentimiento") {
    return (
      <div style={{ background: "white", padding: 32, borderRadius: 12, border: "1px solid #E2E8F0", maxWidth: 800, margin: "0 auto" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
          <h2 style={{ fontSize: 22, color: "#1E293B", margin: 0 }}>📋 Consentimiento Informado</h2>
          <button className="btn-secondary" onClick={onVolver}>← Volver</button>
        </div>

        <div style={{ background: "#F8FAFC", padding: 20, borderRadius: 8, border: "1px solid #CBD5E1", fontSize: 14, lineHeight: 1.6, color: "#334155", maxHeight: 350, overflowY: "auto", marginBottom: 24 }}>
          <h4 style={{ color: "#1E3A8A", marginTop: 0 }}>Batería de Riesgo Psicosocial (Res. 2764 de 2022)</h4>
          <p>
            Por medio de la presente, confirmo que he sido informado(a) sobre los objetivos de la aplicación de la Batería de Evaluación de Riesgo Psicosocial.
          </p>
          <p>
            <strong>Confidencialidad:</strong> Sus respuestas son confidenciales y están protegidas bajo estricto cifrado conforme a la legislación de protección de datos personales. Los resultados serán consolidados y utilizados únicamente para el diagnóstico, prevención y promoción de la salud mental en el entorno laboral.
          </p>
          <p>
            <strong>Voluntariedad:</strong> Su participación es voluntaria y libre de cualquier coacción.
          </p>
          <p>
            Al presionar "Acepto el Consentimiento Informado", usted autoriza el registro de sus respuestas para los fines descritos.
          </p>
        </div>

        {errorMsg && (
          <div style={{ padding: 12, background: "#FEF2F2", color: "#991B1B", borderRadius: 6, marginBottom: 16, fontSize: 14 }}>
            ⚠️ {errorMsg}
          </div>
        )}

        <div style={{ display: "flex", gap: 16, justifyContent: "flex-end" }}>
          <button className="btn-secondary" onClick={onVolver}>Cancelar</button>
          <button className="btn-primary" onClick={handleAceptarConsentimiento}>
            ✓ Acepto el Consentimiento Informado
          </button>
        </div>
      </div>
    );
  }

  if (step === "resultados") {
    return (
      <div style={{ background: "white", padding: 32, borderRadius: 12, border: "1px solid #E2E8F0", maxWidth: 800, margin: "0 auto" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
          <div>
            <h2 style={{ fontSize: 22, color: "#1E293B", margin: 0 }}>✅ Evaluación Completada</h2>
            <p style={{ fontSize: 13, color: "#64748B", margin: "4px 0 0 0" }}>{evaluacionInfo?.nombre}</p>
          </div>
          <button className="btn-secondary" onClick={onVolver}>← Volver</button>
        </div>

        <div style={{ background: "#F0FDF4", border: "1px solid #BBF7D0", padding: 16, borderRadius: 8, marginBottom: 24, color: "#166534" }}>
          🎉 ¡Gracias por completar su evaluación! Sus respuestas han sido procesadas de manera confidencial.
        </div>

        {resultados && resultados.length > 0 && (
          <div>
            <h3 style={{ fontSize: 18, color: "#1E293B", marginBottom: 16 }}>Resumen de Resultados por Dimensión</h3>
            <div style={{ display: "grid", gap: 12 }}>
              {resultados.map((r, idx) => {
                const conf = NIVELES_COLOR[r.nivel] || { bg: "#F1F5F9", text: "#334155", label: r.nivel };
                return (
                  <div key={idx} style={{ background: "#F8FAFC", padding: 16, borderRadius: 8, border: "1px solid #E2E8F0", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div>
                      <div style={{ fontWeight: "600", color: "#1E293B", fontSize: 15 }}>{r.dimension}</div>
                      <div style={{ fontSize: 12, color: "#64748B" }}>Dominio: {r.dominio}</div>
                    </div>
                    <div style={{ textAlign: "right" }}>
                      <span style={{ display: "inline-block", background: conf.bg, color: conf.text, padding: "4px 12px", borderRadius: 20, fontWeight: "bold", fontSize: 13 }}>
                        {r.nivel?.replace("_", " ")}
                      </span>
                      <div style={{ fontSize: 11, color: "#64748B", marginTop: 4 }}>
                        {r.puntajeTransformado !== undefined ? `${r.puntajeTransformado} pts` : ""}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    );
  }

  // CUESTIONARIO COMPONENT
  return (
    <div style={{ background: "white", padding: 32, borderRadius: 12, border: "1px solid #E2E8F0", maxWidth: 850, margin: "0 auto" }}>
      {/* HEADER */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <div>
          <h2 style={{ fontSize: 20, color: "#1E293B", margin: 0 }}>{nombreInstrumento || "Cuestionario BRP"}</h2>
          <p style={{ fontSize: 13, color: "#64748B", margin: "2px 0 0 0" }}>{evaluacionInfo?.nombre}</p>
        </div>
        <button className="btn-secondary" onClick={onVolver}>Guardar y Salir</button>
      </div>

      {/* BARRA DE PROGRESO */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, color: "#64748B", marginBottom: 6 }}>
          <span>Progreso: <strong>{respondidasCount} de {preguntas.length} respondidas</strong></span>
          <span>{progresoPorcentaje}%</span>
        </div>
        <div style={{ height: 8, background: "#E2E8F0", borderRadius: 4, overflow: "hidden" }}>
          <div style={{ height: "100%", width: `${progresoPorcentaje}%`, background: "#1E3A8A", transition: "width 0.3s ease" }} />
        </div>
      </div>

      {errorMsg && (
        <div style={{ padding: 12, background: "#FEF2F2", color: "#991B1B", borderRadius: 6, marginBottom: 20, fontSize: 14 }}>
          ⚠️ {errorMsg}
        </div>
      )}

      {/* NAVIGADOR DE PREGUNTAS (PAGINADOR RAPIDO) */}
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 24 }}>
        {preguntas.map((p, idx) => {
          const respondida = respuestas[p.id] !== undefined;
          const esActual = idx === preguntaActualIdx;
          return (
            <button
              key={p.id}
              onClick={() => setPreguntaActualIdx(idx)}
              style={{
                width: 34,
                height: 34,
                borderRadius: 6,
                border: esActual ? "2px solid #1E3A8A" : "1px solid #CBD5E1",
                background: respondida ? "#DBEAFE" : "#F8FAFC",
                color: esActual ? "#1E3A8A" : respondida ? "#1E40AF" : "#64748B",
                fontWeight: esActual || respondida ? "bold" : "normal",
                cursor: "pointer",
                fontSize: 12,
              }}
            >
              {idx + 1}
            </button>
          );
        })}
      </div>

      {/* TARJETA DE PREGUNTA ACTUAL */}
      {pregActual && (
        <div style={{ background: "#F8FAFC", padding: 24, borderRadius: 10, border: "1px solid #CBD5E1", marginBottom: 24 }}>
          <div style={{ fontSize: 12, textTransform: "uppercase", tracking: 1, color: "#1E3A8A", fontWeight: "bold", marginBottom: 8 }}>
            Pregunta {preguntaActualIdx + 1} de {preguntas.length} — {pregActual.dimension}
          </div>
          <h3 style={{ fontSize: 17, color: "#1E293B", lineHeight: 1.5, marginTop: 0, marginBottom: 20 }}>
            {pregActual.enunciado}
          </h3>

          <div style={{ display: "grid", gap: 10 }}>
            {OPCIONES_LIKERT.filter(
              (op) =>
                op.valor >= (pregActual.valorMinimo ?? 1) &&
                op.valor <= (pregActual.valorMaximo ?? 5)
            ).map((op) => {
              const seleccionada = respuestas[pregActual.id] === op.valor;
              return (
                <button
                  key={op.valor}
                  onClick={() => handleSeleccionarRespuesta(pregActual.id, op.valor)}
                  style={{
                    padding: "12px 18px",
                    borderRadius: 8,
                    border: seleccionada ? "2px solid #1E3A8A" : "1px solid #CBD5E1",
                    background: seleccionada ? "#EFF6FF" : "white",
                    color: seleccionada ? "#1E3A8A" : "#334155",
                    fontWeight: seleccionada ? "bold" : "normal",
                    textAlign: "left",
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    gap: 12,
                    fontSize: 14,
                    transition: "all 0.15s ease",
                  }}
                >
                  <span
                    style={{
                      width: 20,
                      height: 20,
                      borderRadius: "50%",
                      border: seleccionada ? "6px solid #1E3A8A" : "2px solid #CBD5E1",
                      display: "inline-block",
                    }}
                  />
                  {op.etiqueta}
                </button>
              );
            })}
          </div>

          {guardando && (
            <div style={{ fontSize: 12, color: "#64748B", marginTop: 12, fontStyle: "italic" }}>
              💾 Guardando respuesta cifrada...
            </div>
          )}
        </div>
      )}

      {/* BOTONES DE NAVEGACION Y FINALIZACION */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <button
          className="btn-secondary"
          onClick={() => setPreguntaActualIdx((prev) => Math.max(0, prev - 1))}
          disabled={preguntaActualIdx === 0}
        >
          ← Anterior
        </button>

        {preguntaActualIdx < preguntas.length - 1 ? (
          <button
            className="btn-primary"
            onClick={() => setPreguntaActualIdx((prev) => Math.min(preguntas.length - 1, prev + 1))}
          >
            Siguiente →
          </button>
        ) : (
          <button
            className="btn-primary"
            onClick={handleFinalizar}
            disabled={finalizando || respondidasCount < preguntas.length}
            style={{ background: respondidasCount === preguntas.length ? "#059669" : undefined }}
          >
            {finalizando ? "Finalizando..." : "✓ Finalizar Cuestionario"}
          </button>
        )}
      </div>
    </div>
  );
}
