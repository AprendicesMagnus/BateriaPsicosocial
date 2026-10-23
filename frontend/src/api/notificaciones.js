import { request } from "./client";

export function listarNotificaciones(token) {
  return request("/notificaciones", { token });
}

export function marcarNotificacionLeida(token, notificacionId) {
  return request(`/notificaciones/${notificacionId}/leida`, { method: "POST", token });
}
