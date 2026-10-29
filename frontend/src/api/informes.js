import { request, API_URL } from "./client";

export async function listarInformes(token, { evaluacionId = null, tipo = null } = {}) {
  const params = new URLSearchParams();
  if (evaluacionId) params.set("evaluacion_id", evaluacionId);
  if (tipo) params.set("tipo", tipo);
  const query = params.toString();
  return request(query ? `/informes?${query}` : "/informes", { token });
}

export async function generarInformeIndividual(token, evaluacionId, participanteId) {
  return request("/informes/individual", {
    method: "POST",
    body: { evaluacionId, participanteId },
    token,
  });
}

/**
 * Genera y descarga en un ZIP las plantillas Excel llenas, filtradas a la evaluación
 * (y, si se indica, al área) seleccionada. Reemplaza el antiguo informe agrupado en PDF.
 */
export async function descargarInformeAgrupadoZip(token, evaluacionId, areaId = null) {
  const res = await fetch(`${API_URL}/informes/agrupado`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ evaluacionId, areaId }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error || "No fue posible generar el informe agrupado.");
  }

  const disposicion = res.headers.get("content-disposition") || "";
  const nombre = /filename="?([^";]+)"?/i.exec(disposicion)?.[1] || "Informe_Agrupado.zip";

  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = nombre;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.setTimeout(() => window.URL.revokeObjectURL(url), 1000);
}

export async function descargarInforme(token, informeId) {
  const res = await fetch(`${API_URL}/informes/${informeId}/descargar`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error || "No fue posible descargar el informe.");
  }
  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `informe_${informeId}.${res.headers.get("content-type")?.includes("excel") || res.headers.get("content-type")?.includes("spreadsheetml") ? "xlsx" : "pdf"}`;
  document.body.appendChild(a);
  a.click();
  a.remove();
}

export async function fetchVerificacionInforme(codigo) {
  return request(`/informes/verificar/${encodeURIComponent(codigo)}`);
}

/**
 * Descarga en un ZIP las plantillas Excel llenas con los cuestionarios de la empresa
 * (Sociodemográfica, Resultados, Consolidado, Resumen estadístico y respuestas por grupo).
 * Sin evaluacionId incluye todas las evaluaciones de la empresa.
 */
export async function descargarInformesEmpresaZip(token, organizacionId, evaluacionId = null) {
  if (!organizacionId) {
    throw new Error("Selecciona una empresa antes de descargar los informes.");
  }
  const query = evaluacionId ? `?evaluacion_id=${encodeURIComponent(evaluacionId)}` : "";
  const res = await fetch(
    `${API_URL}/informes/empresa/${encodeURIComponent(organizacionId)}/excel/zip${query}`,
    { headers: { Authorization: `Bearer ${token}` } }
  );
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error || "No fue posible descargar los informes.");
  }

  // Nombre que envía el backend (Informes_<empresa>.zip)
  const disposicion = res.headers.get("content-disposition") || "";
  const nombre = /filename="?([^";]+)"?/i.exec(disposicion)?.[1] || "Informes_empresa.zip";

  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = nombre;
  document.body.appendChild(a);
  a.click();
  a.remove();
  // Se libera después de que el navegador inicie la descarga
  window.setTimeout(() => window.URL.revokeObjectURL(url), 1000);
}
