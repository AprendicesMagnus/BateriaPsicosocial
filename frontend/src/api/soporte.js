import { API_URL, request } from "./client";

// Centro de ayuda: enviar un mensaje a soporte (cualquier usuario autenticado).
export const crearTicketSoporte = (token, mensaje) =>
  request("/soporte", { method: "POST", body: { mensaje }, token });

// Panel (Super Administrador): listar y resolver tickets.
export const fetchTicketsSoporte = (token) => request("/soporte", { token });
export const resolverTicketSoporte = (token, id) =>
  request(`/soporte/${id}/resolver`, { method: "POST", token });
export const fetchMisTicketsSoporte = (token) => request("/soporte/mios", { token });
export const responderTicketSoporte = (token, id, respuesta) =>
  request(`/soporte/${id}/responder`, { method: "POST", body: { respuesta }, token });

// Contenido editable del Centro de ayuda.
export const fetchContenidoSoporte = (token) => request("/soporte/contenido", { token });
export const fetchContenidoAdmin = (token) => request("/soporte/contenido/admin", { token });
export const crearContenido = (token, body) => request("/soporte/contenido", { method: "POST", body, token });
export const editarContenido = (token, id, body) => request(`/soporte/contenido/${id}`, { method: "PATCH", body, token });
export const eliminarContenido = (token, id) => request(`/soporte/contenido/${id}`, { method: "DELETE", token });

// Documentos descargables del Centro de ayuda.
export const fetchDocumentosSoporte = (token) => request("/soporte/documentos", { token });
export const fetchDocumentosAdmin = (token) => request("/soporte/documentos/admin", { token });
export const subirDocumentoSoporte = (token, { archivo, titulo, descripcion, activo }) => {
  const form = new FormData();
  form.append("archivo", archivo);
  form.append("titulo", titulo);
  if (descripcion) form.append("descripcion", descripcion);
  form.append("activo", activo ? "true" : "false");
  return request("/soporte/documentos", { method: "POST", body: form, token });
};
export const editarDocumentoSoporte = (token, id, body) =>
  request(`/soporte/documentos/${id}`, { method: "PATCH", body, token });
export const eliminarDocumentoSoporte = (token, id) =>
  request(`/soporte/documentos/${id}`, { method: "DELETE", token });

// La descarga necesita el token (Authorization), así que se baja como blob y se guarda desde aquí.
export async function descargarDocumentoSoporte(token, doc) {
  let respuesta;
  try {
    respuesta = await fetch(`${API_URL}/soporte/documentos/${doc.id}/descargar`, {
      headers: { Authorization: `Bearer ${token}` },
    });
  } catch {
    throw new Error("No se pudo conectar con el servidor.");
  }
  if (!respuesta.ok) {
    const datos = await respuesta.json().catch(() => ({}));
    throw new Error(datos.error || "No se pudo descargar el documento.");
  }
  const url = URL.createObjectURL(await respuesta.blob());
  const enlace = document.createElement("a");
  enlace.href = url;
  enlace.download = doc.nombreArchivo || "documento";
  document.body.appendChild(enlace);
  enlace.click();
  enlace.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
