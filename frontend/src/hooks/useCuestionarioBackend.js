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
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import {
  fetchEvaluaciones,
  fetchCuestionario,
  guardarRespuesta,
  finalizarCuestionario,
  fetchInstrumentosParticipante,
} from "../api/evaluaciones";
import { rutaEnlaceGuardado } from "../api/enlaces";

// Prefijo del código de cada pregunta en la BD. El id numérico de la página + el prefijo
// forman el código: la pregunta 12 de Estrés es "EST_12" (ver seed.py e intralaboral_oficial.py,
// que siembra el intralaboral como "INTRALABORAL_A_12").
const PREFIJOS = {
  ESTRES: "EST_",
  EXTRALABORAL: "EXT_",
  INTRALABORAL_A: "INTRALABORAL_A_",
  INTRALABORAL_B: "INTRALABORAL_B_",
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

// Como el filtro no llega a la BD, un "No" se perdería al recargar la página. Se recuerda en
// sessionStorage por evaluación e instrumento (solo "Sí"/"No", ningún dato del trabajador).
const claveFiltros = (evaluacionId, codigo) => `magnussing:filtros:${evaluacionId}:${codigo}`;

function leerFiltros(evaluacionId, codigo) {
  try {
    const guardado = JSON.parse(sessionStorage.getItem(claveFiltros(evaluacionId, codigo)));
    return guardado && typeof guardado === "object" ? guardado : {};
  } catch {
    return {};
  }
}

function guardarFiltro(evaluacionId, codigo, idFiltro, texto) {
  try {
    const filtros = leerFiltros(evaluacionId, codigo);
    filtros[idFiltro] = texto;
    sessionStorage.setItem(claveFiltros(evaluacionId, codigo), JSON.stringify(filtros));
  } catch {
    // sessionStorage bloqueado: el filtro solo vive en pantalla
  }
}

export function useCuestionarioBackend(codigoEsperado, mapa) {
  const { token, usuario } = useAuth();
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
  // Mensaje flotante al terminar el último cuestionario de la batería
  const [mensajeFinal, setMensajeFinal] = useState(null);
  // Respuestas elegidas antes de que terminara de cargar el cuestionario: { preguntaId: texto }
  const pendientesRef = useRef({});

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
        // Filtros respondidos antes de recargar (incluye los "No", que no dejan respuestas en la BD)
        const previas = { ...leerFiltros(evaluacionId, codigoEsperado) };
        data.preguntas.forEach((p) => {
          mapaUuid[p.codigo] = p.id;
          if (p.respuesta === null || p.respuesta === undefined) return;
          // "EST_12" -> 12, que es el id de la pregunta en la página
          previas[Number(p.codigo.replace(prefijo, ""))] = textoPorValor[p.respuesta];
          // Si hay respuestas de una pregunta condicional, el filtro se había respondido "Sí"
          // (salvo que después lo cambiara a "No": manda lo recordado en sessionStorage)
          if (p.filtro) {
            const idFiltro = Object.keys(FILTROS).find((k) => FILTROS[k] === p.filtro);
            if (previas[idFiltro] === undefined) previas[idFiltro] = "Sí";
          }
        });
        setUuidPorCodigo(mapaUuid);
        setRespuestas(previas);
      })
      .catch((e) => setError(e.message))
      .finally(() => setCargando(false));
  }, [evaluacionId, token, codigoEsperado]);

  // Guarda una respuesta (no filtro) en la BD y muestra el error si falla
  const guardarEnBackend = useCallback(
    async (preguntaId, texto) => {
      // Sin evaluación no se puede guardar; se deja el mensaje de carga (no se sobrescribe)
      if (!evaluacionId) {
        setError((prev) => prev || "No hay una evaluación activa; esta respuesta no se guardó.");
        return;
      }
      const codigo = `${prefijo}${preguntaId}`;
      if (!(codigo in uuidPorCodigo)) {
        // Sin preguntas cargadas la carga falló (p. ej. "restringido al trabajador asignado"):
        // se conserva ese mensaje, que es el que explica el problema, en vez de taparlo
        if (Object.keys(uuidPorCodigo).length === 0) {
          setError((prev) => prev || "No se pudo cargar el cuestionario; la respuesta no se guardó.");
        } else {
          setError(`La pregunta ${preguntaId} no existe en la base de datos.`);
        }
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
        // El backend identifica la pregunta por su código (p. ej. "EST_12"), no por su UUID
        await guardarRespuesta(token, evaluacionId, codigo, valor);
        // Si antes falló un guardado y este funcionó, se quita el aviso de error
        setError(null);
      } catch (e) {
        setError(e.message);
      }
    },
    [uuidPorCodigo, prefijo, token, evaluacionId, mapa]
  );

  // 3. Guarda la respuesta en pantalla y en la BD en cuanto el trabajador hace clic
  const seleccionarRespuesta = useCallback(
    async (preguntaId, texto) => {
      setRespuestas((prev) => ({ ...prev, [preguntaId]: texto }));
      // La pregunta filtro no se guarda como respuesta; se envía al backend al finalizar
      if (FILTROS[preguntaId]) {
        if (evaluacionId) guardarFiltro(evaluacionId, codigoEsperado, preguntaId, texto);
        return;
      }
      // Clic mientras el cuestionario aún se carga: se guarda en cuanto lleguen las preguntas
      // (antes se perdía y quedaba el aviso rojo aunque la carga terminara bien)
      if (cargando && Object.keys(uuidPorCodigo).length === 0) {
        pendientesRef.current[preguntaId] = texto;
        return;
      }
      await guardarEnBackend(preguntaId, texto);
    },
    [uuidPorCodigo, evaluacionId, codigoEsperado, cargando, guardarEnBackend]
  );

  // 3b. Al terminar la carga se guardan las respuestas que se dieron mientras cargaba
  useEffect(() => {
    if (Object.keys(uuidPorCodigo).length === 0) return;
    const pendientes = pendientesRef.current;
    pendientesRef.current = {};
    Object.entries(pendientes).forEach(([preguntaId, texto]) => guardarEnBackend(preguntaId, texto));
  }, [uuidPorCodigo, guardarEnBackend]);

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
        if (usuario?.esInvitado) {
          // Paciente de un enlace: se cierra la evaluación y se manda a la pantalla de
          // "Evaluación finalizada" en vez de dejarlo en el cuestionario ya respondido
          navigate(rutaEnlaceGuardado(), { replace: true });
          return;
        }
        // Trabajador con cuenta propia: aviso flotante en la misma página, se oculta a los 6 segundos
        setMensajeFinal("¡Terminaste todas las encuestas! Gracias por tu participación.");
        setTimeout(() => setMensajeFinal(null), 6000);
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
  }, [respuestas, token, evaluacionId, navigate, usuario]);

  return { respuestas, seleccionarRespuesta, finalizarYNavegar, cargando, error, mensajeFinal };
}
