import { request } from "./client";

// Centro de ayuda: enviar un mensaje a soporte (cualquier usuario autenticado).
export const crearTicketSoporte = (token, mensaje) =>
  request("/soporte", { method: "POST", body: { mensaje }, token });

// Panel (Super Administrador): listar y resolver tickets.
export const fetchTicketsSoporte = (token) => request("/soporte", { token });
export const resolverTicketSoporte = (token, id) =>
  request(`/soporte/${id}/resolver`, { method: "POST", token });

// Contenido editable del Centro de ayuda.
export const fetchContenidoSoporte = (token) => request("/soporte/contenido", { token });
export const fetchContenidoAdmin = (token) => request("/soporte/contenido/admin", { token });
export const crearContenido = (token, body) => request("/soporte/contenido", { method: "POST", body, token });
export const editarContenido = (token, id, body) => request(`/soporte/contenido/${id}`, { method: "PATCH", body, token });
export const eliminarContenido = (token, id) => request(`/soporte/contenido/${id}`, { method: "DELETE", token });
