import { request } from "./client";

export async function fetchIndicadores(token, organizacionId = null, areaId = null) {
  const params = new URLSearchParams();
  if (organizacionId) params.append("organizacion_id", organizacionId);
  if (areaId) params.append("area_id", areaId);
  const query = params.toString() ? `?${params.toString()}` : "";
  return request(`/indicadores${query}`, { token });
}

export async function fetchHistoricoIndicadores(token, organizacionId = null, dimensionId = null) {
  const params = new URLSearchParams();
  if (organizacionId) params.append("organizacion_id", organizacionId);
  if (dimensionId) params.append("dimension_id", dimensionId);
  const query = params.toString() ? `?${params.toString()}` : "";
  return request(`/indicadores/historico${query}`, { token });
}

export async function fetchIndicadoresPorCategoria(token, organizacionId = null, areaId = null) {
  const params = new URLSearchParams();
  if (organizacionId) params.append("organizacion_id", organizacionId);
  if (areaId) params.append("area_id", areaId);
  const query = params.toString() ? `?${params.toString()}` : "";
  return request(`/indicadores/por-categoria${query}`, { token });
}

export async function fetchMapaCalor(token, organizacionId = null, codigo = null) {
  const params = new URLSearchParams();
  if (organizacionId) params.append("organizacion_id", organizacionId);
  if (codigo) params.append("codigo", codigo);
  const query = params.toString() ? `?${params.toString()}` : "";
  return request(`/indicadores/mapa-calor${query}`, { token });
}

export async function fetchAnalisisGrupos(token, organizacionId = null, { codigo = null, variable = null, areaId = null } = {}) {
  const params = new URLSearchParams();
  if (organizacionId) params.append("organizacion_id", organizacionId);
  if (codigo) params.append("codigo", codigo);
  if (variable) params.append("variable", variable);
  if (areaId) params.append("area_id", areaId);
  const query = params.toString() ? `?${params.toString()}` : "";
  return request(`/indicadores/grupos${query}`, { token });
}

export async function fetchAreasOrganizacion(token, organizacionId) {
  return request(`/organizaciones/${organizacionId}/areas`, { token });
}

export async function fetchCompararEvaluaciones(
  token,
  { evaluacionA, evaluacionB, organizacionId = null, codigo = null } = {}
) {
  const params = new URLSearchParams();
  if (evaluacionA) params.append("evaluacion_a", evaluacionA);
  if (evaluacionB) params.append("evaluacion_b", evaluacionB);
  if (organizacionId) params.append("organizacion_id", organizacionId);
  if (codigo) params.append("codigo", codigo);
  const query = params.toString() ? `?${params.toString()}` : "";
  return request(`/indicadores/comparar${query}`, { token });
}
