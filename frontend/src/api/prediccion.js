import { request } from "./client";

export async function fetchAnalisisPredictivo(token, evaluacionId, areaId = null) {
  const path = areaId ? `/prediccion/evaluaciones/${evaluacionId}/prediccion?area_id=${areaId}` : `/prediccion/evaluaciones/${evaluacionId}/prediccion`;
  return request(path, { token });
}
