import { request } from "./client";

export async function fetchReportes(token) {
  return request("/reportes", { token });
}

// Encuestas realizadas por los trabajadores: avance por instrumento y niveles de riesgo.
// Solo ADMINISTRADOR y EVALUADOR_SST (el evaluador ve únicamente las de su organización).
export async function fetchEncuestasRealizadas(token) {
  return request("/reportes/encuestas", { token });
}
