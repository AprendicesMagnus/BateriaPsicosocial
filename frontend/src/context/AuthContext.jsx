import { createContext, useContext, useEffect, useState, startTransition } from "react";
import { fetchMe, cerrarSesionServidor } from "../api/auth";
import { hayPagoEnCurso } from "../utils/pagoPendiente";
import ModalConfirmacion from "../components/ModalConfirmacion";

const AuthContext = createContext(null);
const STORAGE_KEY = "magnussing_token";
const ACTIVIDAD_KEY = "magnussing_ultima_actividad"; // la usa CierreInactividad

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(STORAGE_KEY));
  const [usuario, setUsuario] = useState(null);
  const [loading, setLoading] = useState(Boolean(token));
  const [confirmacionCierre, setConfirmacionCierre] = useState(null);

  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }
    fetchMe(token)
      .then((data) => setUsuario(data.usuario))
      .catch(() => {
        localStorage.removeItem(STORAGE_KEY);
        localStorage.removeItem(ACTIVIDAD_KEY);
        setToken(null);
      })
      .finally(() => setLoading(false));
  }, [token]);

  // Si cualquier petición recibe 401 (token vencido), se cierra la sesión en memoria.
  useEffect(() => {
    const alExpirar = () => {
      localStorage.removeItem(ACTIVIDAD_KEY);
      setToken(null);
      setUsuario(null);
    };
    window.addEventListener("auth:expirada", alExpirar);
    return () => window.removeEventListener("auth:expirada", alExpirar);
  }, []);

  function iniciarSesion(nuevoToken, nuevoUsuario, trustedDeviceToken) {
    localStorage.setItem(STORAGE_KEY, nuevoToken);
    if (trustedDeviceToken) localStorage.setItem("magnussing_dispositivo_confiable", trustedDeviceToken);
    // Sesión nueva = actividad reciente (evita heredar una marca vieja de una sesión anterior)
    localStorage.setItem(ACTIVIDAD_KEY, String(Date.now()));
    // Un inicio de sesión normal ya no es el de un paciente del enlace
    if (!nuevoUsuario?.esInvitado) localStorage.removeItem("magnussing_enlace");
    // Marca para mostrar el saludo de bienvenida solo tras iniciar sesión (no al recargar la página)
    if (!nuevoUsuario?.esInvitado) sessionStorage.setItem("magnussing_bienvenida", "1");
    setToken(nuevoToken);
    setUsuario(nuevoUsuario);
  }

  function actualizarUsuario(nuevoUsuario) {
    setUsuario(nuevoUsuario);
  }

  function ejecutarCierreSesion() {
    const tokenActual = localStorage.getItem(STORAGE_KEY);
    if (tokenActual) cerrarSesionServidor(tokenActual).catch(() => {});
    localStorage.removeItem(STORAGE_KEY);
    localStorage.removeItem(ACTIVIDAD_KEY);
    startTransition(() => {
      setToken(null);
      setUsuario(null);
    });
  }

  function cerrarSesion(opciones) {
    const despues = typeof opciones?.despues === "function" ? opciones.despues : null;
    const forzar = opciones?.forzar === true;

    if (forzar || !hayPagoEnCurso(usuario?.id)) {
      ejecutarCierreSesion();
      despues?.();
      return true;
    }

    setConfirmacionCierre({ despues });
    return false;
  }

  return (
    <AuthContext.Provider
      value={{ token, usuario, loading, iniciarSesion, cerrarSesion, actualizarUsuario }}
    >
      {children}
      <ModalConfirmacion
        abierto={Boolean(confirmacionCierre)}
        titulo="Tienes un pago en proceso"
        mensaje="Si cierras sesión, el pago seguirá su curso y podrás ver su resultado cuando vuelvas a ingresar (en Mi perfil)."
        textoConfirmar="Cerrar sesión de todas formas"
        textoCancelar="Quedarme"
        tipo="normal"
        onConfirmar={() => {
          ejecutarCierreSesion();
          confirmacionCierre?.despues?.();
          setConfirmacionCierre(null);
        }}
        onCancelar={() => setConfirmacionCierre(null)}
      />
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth debe usarse dentro de <AuthProvider>");
  return ctx;
}
