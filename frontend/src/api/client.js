const API_URL = import.meta.env.VITE_API_URL || "http://localhost:4000/api";

async function request(path, { method = "GET", body, token } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;

  let response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch (err) {
    throw new Error(
      "No se pudo conectar con el servidor. Verifica que el backend esté corriendo."
    );
  }

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    // 401 con token = la sesión venció o el token no es válido: se cierra la sesión y se
    // envía al login. Solo aplica si la petición llevaba token; un 401 sin token (p. ej.
    // "Credenciales incorrectas" al iniciar sesión) sigue abajo y se lanza como error normal.
    // Antes se devolvía undefined en todos los 401 y SignIn fallaba al leer data.token.
    if (response.status === 401 && token) {
      localStorage.removeItem("magnussing_token");
      // Ruta real de la página de login (antes apuntaba a "/login", que no existe)
      window.location.href = "/iniciar-sesion";
      throw new Error("Tu sesión expiró. Inicia sesión de nuevo.");
    }
    const error = new Error(data.error || "Ocurrió un error inesperado.");
    error.status = response.status;
    error.payload = data;
    throw error;
  }

  return data;
}

export { request };
export default request;
