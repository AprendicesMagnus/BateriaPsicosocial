import { request } from "./client";

export async function fetchReportes(token) {
  return request("/reportes", { token });
}

// Encuestas realizadas por los trabajadores: avance por instrumento y niveles de riesgo.
// Solo ADMINISTRADOR y EVALUADOR_SST (el evaluador ve únicamente las de su organización).
export async function fetchEncuestasRealizadas(token) {
  return request("/reportes/encuestas", { token });
}

// Respuestas de un participante a cada pregunta, agrupadas por instrumento (se pide al abrirlo).
export async function fetchRespuestasEncuesta(token, participanteId) {
  return request(`/reportes/encuestas/${participanteId}/respuestas`, { token });
}
