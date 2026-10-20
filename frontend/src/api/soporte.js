import { request } from "./client";

// Centro de ayuda: enviar un mensaje a soporte (cualquier usuario autenticado).
export const crearTicketSoporte = (token, mensaje) =>
  request("/soporte", { method: "POST", body: { mensaje }, token });

// Panel (Super Administrador): listar y resolver tickets.
export const fetchTicketsSoporte = (token) => request("/soporte", { token });
export const resolverTicketSoporte = (token, id) =>
  request(`/soporte/${id}/resolver`, { method: "POST", token });
