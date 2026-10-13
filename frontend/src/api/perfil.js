import { request } from "./client";

// Edición de perfil (nombre, apellido, foto). Se envía como multipart/form-data.
export function editarPerfil(token, { nombre, apellido, foto }) {
  const formData = new FormData();
  if (nombre !== undefined) formData.append("nombre", nombre);
  if (apellido !== undefined) formData.append("apellido", apellido);
  if (foto) formData.append("foto", foto);
  return request("/usuarios/me", { method: "PATCH", body: formData, token });
}

// Cambio de contraseña desde el perfil (independiente de "Olvidé mi contraseña").
export function cambiarPassword(token, { passwordActual, passwordNueva }) {
  return request("/usuarios/me/password", {
    method: "POST",
    body: { passwordActual, passwordNueva },
    token,
  });
}

// Solo Super Administrador: nombre completo, correo y rol de todos los usuarios.
export function fetchDirectorio(token, { q = "", limite = 10, desplazamiento = 0 } = {}) {
  const params = new URLSearchParams({ limite, desplazamiento });
  if (q) params.set("q", q);
  return request(`/usuarios/directorio?${params.toString()}`, { token });
}

// Empresas creadas por el usuario actual.
export function fetchMisEmpresas(token) {
  return request("/organizaciones/mias", { token });
}

// Edición y eliminación de una empresa propia ("Mis Empresas").
// La razón social y el NIT están bloqueados: no se envían ni se pueden cambiar.
export function editarMiEmpresa(token, id, { sector, municipio, email, telefono }) {
  return request(`/organizaciones/mias/${id}`, {
    method: "PATCH",
    body: { sector, municipio, email, telefono },
    token,
  });
}

export function eliminarMiEmpresa(token, id) {
  return request(`/organizaciones/mias/${id}`, { method: "DELETE", token });
}

// Psicologo: elegir con cuál de las empresas que creó trabaja (empresa activa).
export function cambiarEmpresaActiva(token, organizacionId) {
  return request("/usuarios/me/empresa-activa", {
    method: "POST",
    body: { organizacionId },
    token,
  });
}

// Usuario responsable de una empresa (solo existe si la creó un Jefe/Administrador).
export function fetchResponsableEmpresa(token, id) {
  return request(`/organizaciones/mias/${id}/responsable`, { token });
}

export function editarResponsableEmpresa(token, id, { nombre, apellido, numeroResolucion }) {
  return request(`/organizaciones/mias/${id}/responsable`, {
    method: "PATCH",
    body: { nombre, apellido, numeroResolucion },
    token,
  });
}
