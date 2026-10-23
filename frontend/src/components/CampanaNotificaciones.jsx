import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { HiOutlineBell } from "react-icons/hi";
import { useAuth } from "../context/AuthContext";
import { listarNotificaciones, marcarNotificacionLeida } from "../api/notificaciones";
import "../styles/CampanaNotificaciones.css";

const INTERVALO_MS = 60000;
const MAX_VISIBLES = 20;

// Ruta a la que lleva cada tipo de notificación. Los tipos que no aparecen aquí solo se marcan como leídos.
const DESTINOS_POR_TIPO = {
  RIESGO_ALTO: "/dashboard",
};

function formatearFecha(iso) {
  const fecha = new Date(iso);
  if (Number.isNaN(fecha.getTime())) return "";
  return fecha.toLocaleString("es-CO", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function CampanaNotificaciones() {
  const { token, usuario } = useAuth();
  const navigate = useNavigate();
  const [abierta, setAbierta] = useState(false);
  const [notificaciones, setNotificaciones] = useState([]);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState("");
  const contenedorRef = useRef(null);

  const visible = Boolean(token) && Boolean(usuario) && !usuario.esInvitado;

  const cargar = useCallback(async () => {
    if (!token) return;
    try {
      const datos = await listarNotificaciones(token);
      setNotificaciones(Array.isArray(datos) ? datos : []);
      setError("");
    } catch {
      setError("No se pudieron cargar las notificaciones.");
    }
  }, [token]);

  useEffect(() => {
    if (!visible) return undefined;
    let activo = true;
    setCargando(true);
    cargar().finally(() => {
      if (activo) setCargando(false);
    });
    const id = setInterval(() => {
      if (document.visibilityState === "visible") cargar();
    }, INTERVALO_MS);
    return () => {
      activo = false;
      clearInterval(id);
    };
  }, [visible, cargar]);

  useEffect(() => {
    if (!abierta) return undefined;
    function alHacerClicFuera(evento) {
      if (contenedorRef.current && !contenedorRef.current.contains(evento.target)) {
        setAbierta(false);
      }
    }
    function alPresionarTecla(evento) {
      if (evento.key === "Escape") setAbierta(false);
    }
    document.addEventListener("mousedown", alHacerClicFuera);
    document.addEventListener("keydown", alPresionarTecla);
    return () => {
      document.removeEventListener("mousedown", alHacerClicFuera);
      document.removeEventListener("keydown", alPresionarTecla);
    };
  }, [abierta]);

  function alternarPanel() {
    if (!abierta) cargar();
    setAbierta(!abierta);
  }

  async function marcarLeida(notificacion) {
    if (notificacion.leida) return;
    setNotificaciones((previas) =>
      previas.map((n) => (n.id === notificacion.id ? { ...n, leida: true } : n))
    );
    try {
      await marcarNotificacionLeida(token, notificacion.id);
    } catch {
      setNotificaciones((previas) =>
        previas.map((n) => (n.id === notificacion.id ? { ...n, leida: false } : n))
      );
    }
  }

  function abrirNotificacion(notificacion) {
    marcarLeida(notificacion);
    const destino = DESTINOS_POR_TIPO[notificacion.tipo];
    if (destino) {
      setAbierta(false);
      navigate(destino);
    }
  }

  async function marcarTodas() {
    const pendientes = notificaciones.filter((n) => !n.leida);
    if (pendientes.length === 0) return;
    setNotificaciones((previas) => previas.map((n) => ({ ...n, leida: true })));
    const resultados = await Promise.allSettled(
      pendientes.map((n) => marcarNotificacionLeida(token, n.id))
    );
    if (resultados.some((r) => r.status === "rejected")) cargar();
  }

  if (!visible) return null;

  const sinLeer = notificaciones.filter((n) => !n.leida).length;
  const visibles = notificaciones.slice(0, MAX_VISIBLES);

  return (
    <div className="campana" ref={contenedorRef}>
      <button
        type="button"
        className="campana__boton"
        onClick={alternarPanel}
        aria-haspopup="true"
        aria-expanded={abierta}
        aria-label={sinLeer > 0 ? `Notificaciones, ${sinLeer} sin leer` : "Notificaciones"}
      >
        <HiOutlineBell size={22} aria-hidden="true" />
        {sinLeer > 0 && <span className="campana__badge">{sinLeer > 9 ? "9+" : sinLeer}</span>}
      </button>

      {abierta && (
        <div className="campana__panel" role="dialog" aria-label="Notificaciones">
          <div className="campana__encabezado">
            <strong>Notificaciones</strong>
            <button
              type="button"
              className="campana__marcar-todas"
              onClick={marcarTodas}
              disabled={sinLeer === 0}
            >
              Marcar todas como leídas
            </button>
          </div>

          {error && <p className="campana__mensaje">{error}</p>}
          {!error && cargando && notificaciones.length === 0 && (
            <p className="campana__mensaje">Cargando...</p>
          )}
          {!error && !cargando && notificaciones.length === 0 && (
            <p className="campana__mensaje">No tienes notificaciones.</p>
          )}

          <ul className="campana__lista">
            {visibles.map((n) => (
              <li key={n.id}>
                <button
                  type="button"
                  className={`campana__item${n.leida ? "" : " campana__item--nueva"}`}
                  onClick={() => abrirNotificacion(n)}
                >
                  <span className="campana__titulo">{n.titulo}</span>
                  <span className="campana__texto">{n.mensaje}</span>
                  <span className="campana__fecha">{formatearFecha(n.fechaEnvio)}</span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
