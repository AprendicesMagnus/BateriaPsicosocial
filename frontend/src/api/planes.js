import { request } from "./client";

// Público (Landing): planes activos.
export const fetchPlanes = () => request("/planes");

// Super Administrador (Panel): todos los planes y su administración.
export const fetchPlanesAdmin = (token) => request("/planes/admin", { token });
export const crearPlan = (token, body) => request("/planes", { method: "POST", body, token });
export const editarPlan = (token, id, body) => request(`/planes/${id}`, { method: "PATCH", body, token });
export const eliminarPlan = (token, id) => request(`/planes/${id}`, { method: "DELETE", token });
