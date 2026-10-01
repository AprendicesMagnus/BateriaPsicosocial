import { request } from "./client";

// ---- Psicólogo (EVALUADOR_SST): enlaces para que sus pacientes respondan sin cuenta ----

export async function fetchEnlaces(token) {
  return request("/enlaces", { token });
}

export async function crearEnlace(token, nombre) {
  return request("/enlaces", { method: "POST", token, body: { nombre } });
}

// Quita el enlace de la lista. Si ya lo usó un paciente, su encuesta se conserva.
export async function eliminarEnlace(token, evaluacionId) {
  return request(`/enlaces/${evaluacionId}`, { method: "DELETE", token });
}

// ---- Paciente: endpoints públicos, sin sesión ----

export async function fetchEnlacePublico(tokenEnlace) {
  return request(`/enlaces/publico/${tokenEnlace}`);
}

// Crea el paciente invitado y devuelve { token, usuario, evaluacionId }
export async function iniciarEnlace(tokenEnlace, aceptaConsentimiento) {
  return request(`/enlaces/publico/${tokenEnlace}/iniciar`, {
    method: "POST",
    body: { aceptaConsentimiento },
  });
}

// Enlace con el que entró el paciente en este navegador, para volver a él
// (al terminar la batería o si intenta abrir una página interna)
export const CLAVE_ENLACE = "magnussing_enlace";

export function rutaEnlaceGuardado() {
  try {
    const tokenEnlace = localStorage.getItem(CLAVE_ENLACE);
    return tokenEnlace ? `/responder/${tokenEnlace}` : "/";
  } catch {
    return "/";
  }
}
