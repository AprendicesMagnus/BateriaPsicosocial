const API_URL = import.meta.env.VITE_API_URL || "http://localhost:4000/api";

async function request(path, { method = "GET", body, token } = {}) {
  const esFormData = typeof FormData !== "undefined" && body instanceof FormData;
  // Con FormData el navegador agrega solo el Content-Type (multipart + boundary).
  const headers = esFormData ? {} : { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;

  let response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      method,
      headers,
      body: body ? (esFormData ? body : JSON.stringify(body)) : undefined,
    });
  } catch (err) {
    throw new Error(
      "No se pudo conectar con el servidor. Verifica que el backend esté corriendo."
    );
  }

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    // 401 con sesión enviada = token vencido o inválido. No se redirige a la fuerza (antes
    // llevaba a una ruta inexistente y dejaba la pantalla en blanco): se limpia el token y se
    // avisa al AuthContext, y las rutas protegidas se encargan de mandar al login.
    // Sin token (login, Google, registro) es un rechazo normal: se muestra el mensaje del backend.
    if (response.status === 401 && token) {
      localStorage.removeItem("magnussing_token");
      window.dispatchEvent(new Event("auth:expirada"));
      const expirada = new Error("Tu sesión expiró. Inicia sesión de nuevo.");
      expirada.status = 401;
      throw expirada;
    }
    const error = new Error(data.error || "Ocurrió un error inesperado.");
    error.status = response.status;
    error.payload = data;
    throw error;
  }

  return data;
}

// Convierte una ruta del backend (p. ej. /api/uploads/avatars/x.jpg) en una URL completa.
function urlArchivo(ruta) {
  if (!ruta) return null;
  if (/^https?:\/\//i.test(ruta)) return ruta;
  return `${new URL(API_URL, window.location.origin).origin}${ruta}`;
}

export { request, urlArchivo };
export default request;