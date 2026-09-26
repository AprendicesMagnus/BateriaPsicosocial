import { request } from "./client";

export async function fetchIndicadores(token, organizacionId = null) {
  const path = organizacionId ? `/indicadores?organizacion_id=${organizacionId}` : "/indicadores";
  return request(path, { token });
}

export async function fetchHistoricoIndicadores(token, organizacionId = null, dimensionId = null) {
  const params = new URLSearchParams();
  if (organizacionId) params.append("organizacion_id", organizacionId);
  if (dimensionId) params.append("dimension_id", dimensionId);
  const query = params.toString() ? `?${params.toString()}` : "";
  return request(`/indicadores/historico${query}`, { token });
}

export async function fetchIndicadoresPorCategoria(token, organizacionId = null) {
  const path = organizacionId ? `/indicadores/por-categoria?organizacion_id=${organizacionId}` : "/indicadores/por-categoria";
  return request(path, { token });
}

