import { request } from "./client";

export async function fetchSeguimientosRecomendaciones(token, organizacionId = null) {
  const path = organizacionId ? `/seguimiento-recomendaciones?organizacion_id=${organizacionId}` : "/seguimiento-recomendaciones";
  return request(path, { token });
}

export async function guardarSeguimientoRecomendacion(token, payload) {
  return request("/seguimiento-recomendaciones", {
    method: "POST",
    token,
    body: payload,
  });
}
