import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import Toast from "./Toast";

// Minutos sin actividad antes de cerrar la sesión. Por defecto 120 (2 horas).
// Para probar: VITE_INACTIVIDAD_MINUTOS=1 en frontend/.env (y reiniciar `npm run dev`).
const MINUTOS = Number(import.meta.env.VITE_INACTIVIDAD_MINUTOS) || 120;
const LIMITE_MS = MINUTOS * 60 * 1000;

const CLAVE_ACTIVIDAD = "magnussing_ultima_actividad"; // compartida entre pestañas
const CLAVE_TOKEN = "magnussing_token";
const REVISION_MS = 30 * 1000; // cada cuánto se revisa
const ESCRITURA_MIN_MS = 15 * 1000; // no escribir en localStorage más de 1 vez cada 15 s
const EVENTOS = ["mousedown", "mousemove", "keydown", "scroll", "touchstart", "click"];

const leerUltimaActividad = () => {
  try {
    return Number(localStorage.getItem(CLAVE_ACTIVIDAD)) || 0;
  } catch {
    return 0;
  }
};

const guardarActividad = (momento) => {
  try {
    localStorage.setItem(CLAVE_ACTIVIDAD, String(momento));
  } catch {
    /* almacenamiento no disponible: se ignora */
  }
};

// Cierra la sesión tras un periodo sin actividad y lleva al inicio de sesión.
// Se monta una sola vez dentro de <BrowserRouter> y no renderiza nada (salvo el aviso).
export default function CierreInactividad() {
  const { token, usuario, loading, cerrarSesion } = useAuth();
  const navigate = useNavigate();
  const [aviso, setAviso] = useState("");
  const ultimaEscritura = useRef(0);

  // El paciente que responde por enlace tiene su propio flujo: no se le cierra la sesión.
  // Se espera a que termine de cargar el usuario para saber si es invitado antes de actuar.
  const activo = !loading && Boolean(token) && !usuario?.esInvitado;

  useEffect(() => {
    if (!activo) return undefined;

    function cerrarPorInactividad() {
      try {
        localStorage.removeItem(CLAVE_ACTIVIDAD);
      } catch {
        /* se ignora */
      }
      cerrarSesion();
      navigate("/iniciar-sesion", { replace: true });
      setAviso("Tu sesión se cerró por inactividad. Inicia sesión de nuevo.");
    }

    function revisar() {
      // Otra pestaña cerró la sesión: se refleja en esta.
      if (!localStorage.getItem(CLAVE_TOKEN)) {
        cerrarSesion();
        navigate("/iniciar-sesion", { replace: true });
        return;
      }
      const ultima = leerUltimaActividad();
      if (ultima && Date.now() - ultima >= LIMITE_MS) cerrarPorInactividad();
    }

    function registrarActividad() {
      const ahora = Date.now();
      if (ahora - ultimaEscritura.current < ESCRITURA_MIN_MS) return;
      ultimaEscritura.current = ahora;
      guardarActividad(ahora);
    }

    function alVolverAPestana() {
      if (document.visibilityState === "visible") revisar();
    }

    // Al abrir la app (o recargar) se revisa primero: si el navegador estuvo cerrado
    // más tiempo del permitido, la sesión guardada ya no sirve.
    const ultimaGuardada = leerUltimaActividad();
    if (ultimaGuardada && Date.now() - ultimaGuardada >= LIMITE_MS) {
      cerrarPorInactividad();
      return undefined;
    }
    ultimaEscritura.current = 0;
    registrarActividad();

    EVENTOS.forEach((evento) => window.addEventListener(evento, registrarActividad, { passive: true }));
    document.addEventListener("visibilitychange", alVolverAPestana);
    const intervalo = setInterval(revisar, REVISION_MS);

    return () => {
      EVENTOS.forEach((evento) => window.removeEventListener(evento, registrarActividad));
      document.removeEventListener("visibilitychange", alVolverAPestana);
      clearInterval(intervalo);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activo]);

  // Sin sesión no debe quedar ninguna marca de actividad (evita falsos cierres al volver a entrar).
  useEffect(() => {
    if (!loading && !token) {
      try {
        localStorage.removeItem(CLAVE_ACTIVIDAD);
      } catch {
        /* se ignora */
      }
    }
  }, [loading, token]);

  // El aviso se quita solo.
  useEffect(() => {
    if (!aviso) return undefined;
    const espera = setTimeout(() => setAviso(""), 6000);
    return () => clearTimeout(espera);
  }, [aviso]);

  return aviso ? <Toast mensaje={aviso} tipo="info" duracion={6000} /> : null;
}
