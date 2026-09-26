import { request } from "./client";

export async function fetchEvaluaciones(token) {
  return request("/evaluaciones", { token });
}

export async function fetchEvaluacionDetalle(token, evaluacionId) {
  return request(`/evaluaciones/${evaluacionId}`, { token });
}

export async function registrarConsentimiento(token, evaluacionId) {
  return request(`/evaluaciones/${evaluacionId}/consentimiento`, {
    method: "POST",
    token,
  });
}

export async function fetchCuestionario(token, evaluacionId) {
  return request(`/evaluaciones/${evaluacionId}/cuestionario`, { token });
}

export async function guardarRespuesta(token, evaluacionId, preguntaId, valor) {
  return request(`/evaluaciones/${evaluacionId}/respuestas`, {
    method: "POST",
    token,
    body: { preguntaId, valor },
  });
}

export async function finalizarCuestionario(token, evaluacionId) {
  return request(`/evaluaciones/${evaluacionId}/finalizar-cuestionario`, {
    method: "POST",
    token,
  });
}

export async function fetchResultadosTrabajador(token, evaluacionId) {
  return request(`/evaluaciones/${evaluacionId}/resultados`, { token });
}

export async function guardarFichaDatos(token, evaluacionId, data) {
  return request(`/evaluaciones/${evaluacionId}/ficha`, {
    method: "POST",
    token,
    body: data,
  });
}

export async function fetchInstrumentosParticipante(token, evaluacionId) {
  return request(`/evaluaciones/${evaluacionId}/instrumentos`, { token });
}

