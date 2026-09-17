import { request } from "./client";

export async function generarInformeIndividual(token, evaluacionId, participanteId) {
  return request("/informes/individual", {
    method: "POST",
    body: { evaluacionId, participanteId },
    token,
  });
}

export async function generarInformeAgrupado(token, evaluacionId, areaId = null, formato = "PDF") {
  return request("/informes/agrupado", {
    method: "POST",
    body: { evaluacionId, areaId, formato },
    token,
  });
}

export async function descargarInforme(token, informeId) {
  const API_URL = import.meta.env.VITE_API_URL || "http://localhost:4000/api";
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
