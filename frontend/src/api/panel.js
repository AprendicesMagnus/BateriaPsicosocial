import { request, API_URL } from "./client";

export async function fetchPanel(token) {
  return request("/panel", { token });
}

export async function fetchEvolucionPanel(token, meses = 12) {
  return request(`/panel/evolucion?meses=${meses}`, { token });
}

export async function descargarExportacionPanel(token, tabla, { filtro, buscar } = {}) {
  const params = new URLSearchParams();
  if (filtro) params.set("filtro", filtro);
  if (buscar) params.set("buscar", buscar);
  const query = params.toString() ? `?${params.toString()}` : "";

  const res = await fetch(`${API_URL}/panel/exportar/${tabla}${query}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error || "No fue posible exportar la tabla.");
  }
  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `panel_${tabla}.xlsx`;
  document.body.appendChild(a);
  a.click();
  a.remove();
}


export async function fetchHistorialComprasTienda(token) {
  return request("/panel/historial-compras", { token });
}
