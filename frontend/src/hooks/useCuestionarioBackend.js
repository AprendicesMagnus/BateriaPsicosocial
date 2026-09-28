import { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import {
  fetchEvaluaciones,
  fetchCuestionario,
  fetchInstrumentosParticipante,
  guardarRespuesta,
  finalizarCuestionario,
} from "../api/evaluaciones";

export function useCuestionarioBackend(codigoInstrumento, opcionValoresMap) {
  const navigate = useNavigate();
  const location = useLocation();
  const { token } = useAuth();

  const [evaluacionId, setEvaluacionId] = useState(location.state?.evaluacionId || null);
  const [preguntasBackend, setPreguntasBackend] = useState([]);
  const [loading, setLoading] = useState(true);
  const [errorBackend, setErrorBackend] = useState(null);
  const [respuestas, setRespuestas] = useState({});

  useEffect(() => {
    let cancelado = false;
    async function init() {
      if (!token) {
        setLoading(false);
        return;
      }
      setLoading(true);
      try {
        let currentEvalId = evaluacionId;
        if (!currentEvalId) {
          const evs = await fetchEvaluaciones(token);
          const activa = evs.find((e) => e.estado !== "FINALIZADA") || evs[0];
          if (activa) {
            currentEvalId = activa.id;
            setEvaluacionId(activa.id);
          }
        }

        if (!currentEvalId) {
          setErrorBackend("No tienes evaluaciones asignadas activas.");
          setLoading(false);
          return;
        }

        // Verificar instrumentos asignados al participante
        const instrumentos = await fetchInstrumentosParticipante(token, currentEvalId);
        
        // Redirección si la forma asignada de Intralaboral difiere de la ruta actual
        const instIntra = instrumentos.find(
          (i) => i.codigo === "INTRALABORAL_A" || i.codigo === "INTRALABORAL_B"
        );
        if (codigoInstrumento.startsWith("INTRALABORAL") && instIntra) {
          if (instIntra.codigo !== codigoInstrumento) {
            const rutaTarget =
              instIntra.codigo === "INTRALABORAL_A"
                ? "/cuestionario-intralaboral"
                : "/cuestionario-intralaboralB";
            navigate(rutaTarget, { state: { evaluacionId: currentEvalId }, replace: true });
            return;
          }
        }

        // Cargar cuestionario del backend
        try {
          const questData = await fetchCuestionario(token, currentEvalId);
          if (!cancelado && questData) {
            // Validación de código devuelto contra la página actual
            if (questData.codigo && questData.codigo !== codigoInstrumento) {
              let ruta = "/dashboard";
              if (questData.codigo === "FICHA_DATOS") ruta = "/ficha-datos-generales";
              else if (questData.codigo === "ESTRES") ruta = "/cuestionario-estres";
              else if (questData.codigo === "EXTRALABORAL") ruta = "/cuestionario-extralaboral";
              else if (questData.codigo === "INTRALABORAL_A") ruta = "/cuestionario-intralaboral";
              else if (questData.codigo === "INTRALABORAL_B") ruta = "/cuestionario-intralaboralB";

              navigate(ruta, { state: { evaluacionId: currentEvalId }, replace: true });
              return;
            }

            if (questData.preguntas) {
              setPreguntasBackend(questData.preguntas);

              // Cargar respuestas previamente guardadas si existen
              const mapInicial = {};
              questData.preguntas.forEach((p, idx) => {
                if (p.respuesta !== null && p.respuesta !== undefined) {
                  const opTexto = Object.keys(opcionValoresMap).find(
                    (k) => opcionValoresMap[k] === p.respuesta
                  );
                  if (opTexto) {
                    mapInicial[idx + 1] = opTexto;
                  }
                }
              });
              setRespuestas(mapInicial);
            }
          }
        } catch (qErr) {
          // Ignorar si aún no hay cuestionario abierto o consentimiento pendiente
        }
      } catch (err) {
        if (!cancelado) {
          setErrorBackend(err.message || "Error al cargar la información del cuestionario.");
        }
      } finally {
        if (!cancelado) setLoading(false);
      }
    }

    init();
    return () => {
      cancelado = true;
    };
  }, [token, evaluacionId, codigoInstrumento]);

  const seleccionarRespuesta = async (preguntaId1Based, opcionTexto) => {
    setRespuestas((prev) => ({ ...prev, [preguntaId1Based]: opcionTexto }));

    if (!token || !evaluacionId || !preguntasBackend.length) return;

    const idx = preguntaId1Based - 1;
    const pBackend = preguntasBackend[idx];
    if (!pBackend) return;

    const valorNumerico = opcionValoresMap[opcionTexto];
    if (valorNumerico !== undefined) {
      try {
        await guardarRespuesta(token, evaluacionId, pBackend.id, valorNumerico);
      } catch (err) {
        console.error("Error guardando respuesta:", err);
      }
    }
  };

  const finalizarYNavegar = async () => {
    if (!token || !evaluacionId) return;

    try {
      const instrumentos = await fetchInstrumentosParticipante(token, evaluacionId);
      const pendientesLocal = instrumentos.filter(
        (i) => i.estado !== "COMPLETADA" && i.codigo !== codigoInstrumento
      );

      if (pendientesLocal.length === 0) {
        try {
          await finalizarCuestionario(token, evaluacionId);
          alert("¡Has completado todos los instrumentos de la evaluación!");
          navigate("/dashboard");
        } catch (fErr) {
          if (fErr.detail && fErr.detail.pendientes) {
            alert(`Faltan preguntas por responder: ${fErr.detail.pendientes.join(", ")}`);
          } else {
            alert(`Error al finalizar la evaluación: ${fErr.message}`);
          }
        }
      } else {
        const proximo = pendientesLocal[0].codigo;
        let ruta = "/dashboard";
        if (proximo === "ESTRES") ruta = "/cuestionario-estres";
        else if (proximo === "EXTRALABORAL") ruta = "/cuestionario-extralaboral";
        else if (proximo === "INTRALABORAL_A") ruta = "/cuestionario-intralaboral";
        else if (proximo === "INTRALABORAL_B") ruta = "/cuestionario-intralaboralB";

        alert("Se han guardado tus respuestas. Pasando al siguiente instrumento.");
        navigate(ruta, { state: { evaluacionId } });
      }
    } catch (err) {
      alert(`Error al finalizar el cuestionario: ${err.message}`);
    }
  };

  return {
    token,
    evaluacionId,
    respuestas,
    loading,
    errorBackend,
    seleccionarRespuesta,
    finalizarYNavegar,
  };
}
