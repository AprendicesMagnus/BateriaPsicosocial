/**
 * Hook que conecta las páginas de cuestionarios (Estrés, Extralaboral, Intralaboral A/B)
 * con el backend.
 *
 * - Carga el instrumento pendiente del trabajador y sus respuestas ya guardadas.
 * - Guarda cada respuesta en la BD en cuanto el trabajador hace clic.
 * - Al finalizar, cierra el instrumento y navega al siguiente pendiente.
 *
 * Uso en una página:
 *   const { respuestas, seleccionarRespuesta, finalizarYNavegar, cargando, error } =
 *     useCuestionarioBackend("ESTRES", MAPA_ESTRES);
 *
 * @param {string} codigoEsperado Código del instrumento en BD (ESTRES, EXTRALABORAL, INTRALABORAL_A, INTRALABORAL_B).
 * @param {Record<string, number>} mapa Texto de la opción -> valor numérico que se guarda.
 */
import { useCallback, useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import {
  fetchEvaluaciones,
  fetchCuestionario,
  guardarRespuesta,
  finalizarCuestionario,
  fetchInstrumentosParticipante,
} from "../api/evaluaciones";

// Prefijo del código de cada pregunta en la BD. El id numérico de la página + el prefijo
// forman el código: la pregunta 12 de Estrés es "EST_12" (ver seed.py e intralaboral.py).
const PREFIJOS = {
  ESTRES: "EST_",
  EXTRALABORAL: "EXT_",
  INTRALABORAL_A: "INTA_",
  INTRALABORAL_B: "INTB_",
};

// Ruta del frontend de cada instrumento, para redirigir al que esté pendiente
// (también la usa la página del enlace del paciente para "Continuar")
export const RUTAS = {
  FICHA_DATOS: "/ficha-datos-generales",
  ESTRES: "/cuestionario-estres",
  EXTRALABORAL: "/cuestionario-extralaboral",
  INTRALABORAL_A: "/cuestionario-intralaboral",
  INTRALABORAL_B: "/cuestionario-intralaboralB",
};

// id de la pregunta filtro en la página -> valor de Pregunta.filtro en la BD.
// Las preguntas filtro ("¿Atiende clientes?", "¿Es jefe?") no se guardan como respuesta:
// solo deciden qué preguntas condicionales se muestran y se exigen.
const FILTROS = { clientes: "CLIENTES", jefe: "JEFE" };

export function useCuestionarioBackend(codigoEsperado, mapa) {
  const { token } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  // La Ficha de datos y el paso entre cuestionarios envían el id en location.state
  const [evaluacionId, setEvaluacionId] = useState(location.state?.evaluacionId || null);
  // Código de pregunta ("EST_12") -> UUID de la pregunta en la BD
  const [uuidPorCodigo, setUuidPorCodigo] = useState({});
  // id de la pregunta en la página -> texto de la opción elegida (lo que pintan las páginas)
  const [respuestas, setRespuestas] = useState({});
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState(null);

  const prefijo = PREFIJOS[codigoEsperado];

  // Mapa inverso (valor numérico -> texto) para pintar las respuestas guardadas al recargar.
  // Si dos textos tienen el mismo valor, se usa el primero del mapa.
  const textoPorValor = useMemo(() => {
    const inverso = {};
    Object.entries(mapa).forEach(([texto, valor]) => {
      if (!(valor in inverso)) inverso[valor] = texto;
    });
    return inverso;
  }, [mapa]);

  // 1. Si se entró directo a la página (sin location.state), se toma la evaluación activa del trabajador
  useEffect(() => {
    if (evaluacionId || !token) return;
    fetchEvaluaciones(token)
      .then((evs) => {
        const activa = evs.find((e) => e.estado !== "FINALIZADA") || evs[0];
        if (activa) setEvaluacionId(activa.id);
        else {
          // Sin evaluación el backend no tiene dónde guardar las respuestas
          setError(
            "No tienes una evaluación asignada. Pide al evaluador que te agregue a una evaluación " +
              "e inicia sesión con tu usuario de trabajador."
          );
          setCargando(false);
        }
      })
      .catch((e) => {
        setError(e.message);
        setCargando(false);
      });
  }, [token, evaluacionId]);

  // 2. Se carga el instrumento pendiente y las respuestas que ya estaban guardadas
  useEffect(() => {
    if (!evaluacionId || !token) return;
    setCargando(true);
    fetchCuestionario(token, evaluacionId)
      .then((data) => {
        // El backend siempre devuelve el primer instrumento pendiente. Si no es el de esta
        // página (p. ej. entró a Extralaboral sin terminar Estrés), se redirige al correcto.
        if (data.codigo !== codigoEsperado) {
          navigate(data.codigo ? RUTAS[data.codigo] : "/dashboard", {
            replace: true,
            state: { evaluacionId },
          });
          return;
        }
        const mapaUuid = {};
        const previas = {};
        data.preguntas.forEach((p) => {
          mapaUuid[p.codigo] = p.id;
          if (p.respuesta === null || p.respuesta === undefined) return;
          // "EST_12" -> 12, que es el id de la pregunta en la página
          previas[Number(p.codigo.replace(prefijo, ""))] = textoPorValor[p.respuesta];
          // Si hay respuestas de una pregunta condicional, el filtro se había respondido "Sí"
          if (p.filtro) {
            const idFiltro = Object.keys(FILTROS).find((k) => FILTROS[k] === p.filtro);
            previas[idFiltro] = "Sí";
          }
        });
        setUuidPorCodigo(mapaUuid);
        setRespuestas(previas);
      })
      .catch((e) => setError(e.message))
      .finally(() => setCargando(false));
  }, [evaluacionId, token, codigoEsperado]);

  // 3. Guarda la respuesta en pantalla y en la BD en cuanto el trabajador hace clic
  const seleccionarRespuesta = useCallback(
    async (preguntaId, texto) => {
      setRespuestas((prev) => ({ ...prev, [preguntaId]: texto }));
      // La pregunta filtro solo vive en pantalla; se envía al backend al finalizar
      if (FILTROS[preguntaId]) return;
      // Sin evaluación no se puede guardar; se deja el mensaje de carga (no se sobrescribe)
      if (!evaluacionId) {
        setError((prev) => prev || "No hay una evaluación activa; esta respuesta no se guardó.");
        return;
      }
      const uuid = uuidPorCodigo[`${prefijo}${preguntaId}`];
      if (!uuid) {
        setError(`La pregunta ${preguntaId} no existe en la base de datos.`);
        return;
      }
      // La página debe enviar el TEXTO de la opción; si no está en el mapa no hay valor numérico
      // y el backend lo rechazaría con "El campo 'valor' es obligatorio"
      const valor = mapa[texto];
      if (valor === undefined) {
        setError(`La opción "${texto}" no tiene un valor configurado; la respuesta no se guardó.`);
        return;
      }
      try {
        await guardarRespuesta(token, evaluacionId, uuid, valor);
        // Si antes falló un guardado y este funcionó, se quita el aviso de error
        setError(null);
      } catch (e) {
        setError(e.message);
      }
    },
    [uuidPorCodigo, prefijo, token, evaluacionId, mapa]
  );

  // 4. Cierra el instrumento en el backend y navega al siguiente pendiente (o al dashboard)
  const finalizarYNavegar = useCallback(async () => {
    // Sin evaluación no hay nada que finalizar en el backend
    if (!evaluacionId) {
      setError((prev) => prev || "No hay una evaluación activa; no se puede finalizar el cuestionario.");
      window.scrollTo({ top: 0, behavior: "smooth" });
      return;
    }
    // Respuestas a las preguntas filtro: { CLIENTES: false, JEFE: true }
    const filtros = {};
    Object.entries(FILTROS).forEach(([idPagina, codigo]) => {
      if (respuestas[idPagina] !== undefined) filtros[codigo] = respuestas[idPagina] === "Sí";
    });
    try {
      const res = await finalizarCuestionario(token, evaluacionId, filtros);
      // completadoTotal = true cuando era el último instrumento de la batería
      if (res.completadoTotal) {
        alert("¡Completaste toda la batería!");
        navigate("/dashboard");
        return;
      }
      const instrumentos = await fetchInstrumentosParticipante(token, evaluacionId);
      const siguiente = instrumentos.find((i) => i.estado !== "COMPLETADA");
      navigate(siguiente ? RUTAS[siguiente.codigo] : "/dashboard", { state: { evaluacionId } });
    } catch (e) {
      // El backend devuelve { error, pendientes: [...] } cuando faltan preguntas
      const pendientes = e.payload?.pendientes;
      setError(pendientes ? `Faltan ${pendientes.length} pregunta(s) por responder.` : e.message);
      // Sube al inicio para que el trabajador vea el aviso
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  }, [respuestas, token, evaluacionId, navigate]);

  return { respuestas, seleccionarRespuesta, finalizarYNavegar, cargando, error };
}
