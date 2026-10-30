import { request, API_URL } from "./client";

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

// Psicologo: registrar su número de resolución (6 dígitos).
export function guardarMiResolucion(token, numeroResolucion) {
  return request("/usuarios/me/resolucion", { method: "POST", body: { numeroResolucion }, token });
}

// Super Administrador: marcar o quitar la verificación del número de resolución de un usuario.
export function verificarResolucion(token, usuarioId, verificada) {
  return request(`/usuarios/${usuarioId}/verificar-resolucion`, { method: "POST", body: { verificada }, token });
}

// Panel (Super Administrador): invitar, editar y reenviar el código de verificación de un usuario.
export const invitarUsuario = (token, body) => request("/usuarios/invitar", { method: "POST", body, token });
export const editarUsuarioAdmin = (token, id, body) => request(`/usuarios/${id}`, { method: "PATCH", body, token });
export const reenviarCodigoVerificacion = (email) =>
  request("/auth/resend-code", { method: "POST", body: { email, tipo: "VERIFICACION_EMAIL" } });

// Derechos del titular: descarga una copia de los datos propios como archivo JSON.
export async function descargarMisDatos(token) {
  let res;
  try {
    res = await fetch(`${API_URL}/usuarios/me/datos`, {
      headers: { Authorization: `Bearer ${token}` },
    });
  } catch {
    throw new Error("No se pudo conectar con el servidor. Verifica que el backend esté corriendo.");
  }
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error || "No fue posible descargar tus datos.");
  }
  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const fecha = new Date().toISOString().slice(0, 10).replace(/-/g, "");
  const a = document.createElement("a");
  a.href = url;
  a.download = `mis-datos-magnussig-${fecha}.json`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

// Derechos del titular: solicita la eliminacion de la cuenta (llega al Centro de ayuda). El motivo es opcional.
export const solicitarEliminacionCuenta = (token, motivo) =>
  request("/usuarios/me/solicitar-eliminacion", { method: "POST", body: motivo ? { motivo } : {}, token });
