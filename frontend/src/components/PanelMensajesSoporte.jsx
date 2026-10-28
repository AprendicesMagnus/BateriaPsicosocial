import { Fragment, useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { fetchTicketsSoporte, resolverTicketSoporte, responderTicketSoporte } from "../api/soporte";
import { etiquetaRol } from "../utils/roles";
import { usePaginacion } from "../hooks/usePaginacion";
import Paginador from "./Paginador";
import "../styles/Planes.css";
import "../styles/PanelAcciones.css";

const FILTROS_ESTADO = [
  { clave: "TODOS", label: "Todos" },
  { clave: "PENDIENTE", label: "Pendientes" },
  { clave: "RESUELTO", label: "Resueltos" },
];

function formatearFecha(iso) {
  if (!iso) return "";
  const f = new Date(iso);
  if (Number.isNaN(f.getTime())) return "";
  return f.toLocaleString("es-CO", { dateStyle: "medium", timeStyle: "short" });
}

export default function PanelMensajesSoporte({ selector = null }) {
  const { token } = useAuth();
  const [tickets, setTickets] = useState([]);
  const [filtroEstado, setFiltroEstado] = useState("TODOS");
  const [ticketEnEdicion, setTicketEnEdicion] = useState(null);
  const [textoRespuesta, setTextoRespuesta] = useState("");
  const [guardando, setGuardando] = useState(false);
  const [mensaje, setMensaje] = useState(null);

  const cargar = () =>
    fetchTicketsSoporte(token)
      .then((res) => setTickets(Array.isArray(res) ? res : []))
      .catch((err) =>
        setMensaje({ tipo: "error", texto: err.message || "No se pudieron cargar los mensajes de soporte." })
      );

  useEffect(() => {
    if (token) cargar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const ticketsFiltrados = tickets.filter((t) => {
    if (filtroEstado === "TODOS") return true;
    return t.estado === filtroEstado;
  });

  const pag = usePaginacion(ticketsFiltrados, 10, [filtroEstado]);

  async function handleResolver(ticketId) {
    setMensaje(null);
    try {
      await resolverTicketSoporte(token, ticketId);
      setMensaje({ tipo: "ok", texto: "Ticket marcado como resuelto." });
      await cargar();
    } catch (err) {
      setMensaje({ tipo: "error", texto: err.message || "No se pudo marcar como resuelto." });
    }
  }

  async function handleResponder(e, ticketId) {
    e.preventDefault();
    const texto = textoRespuesta.trim();
    if (!texto) {
      setMensaje({ tipo: "error", texto: "La respuesta no puede estar vacía." });
      return;
    }
    setGuardando(true);
    setMensaje(null);
    try {
      await responderTicketSoporte(token, ticketId, texto);
      setTicketEnEdicion(null);
      setTextoRespuesta("");
      setMensaje({ tipo: "ok", texto: "Respuesta enviada correctamente." });
      await cargar();
    } catch (err) {
      setMensaje({ tipo: "error", texto: err.message || "No se pudo enviar la respuesta." });
    } finally {
      setGuardando(false);
    }
  }

  return (
    <section id="soporte-mensajes" className="adm-card">
      <div className="adm-card__head">
        <div>
          <h2>Mensajes de soporte</h2>
          <span>Mensajes enviados por los usuarios desde el Centro de ayuda.</span>
        </div>
        <div className="plan-form__acciones">
          {selector}
          <select
            className="adm-input"
            value={filtroEstado}
            onChange={(e) => {
              setFiltroEstado(e.target.value);
              setTicketEnEdicion(null);
            }}
          >
            {FILTROS_ESTADO.map((f) => (
              <option key={f.clave} value={f.clave}>
                {f.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {mensaje && <div className={`plan-mensaje plan-mensaje--${mensaje.tipo}`}>{mensaje.texto}</div>}

      <div className="adm-tabla-wrap">
        <table className="adm-tabla">
          <thead>
            <tr>
              <th>Usuario</th>
              <th>Fecha</th>
              <th>Mensaje</th>
              <th>Estado</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {pag.items.map((t) => {
              const tieneRespuesta = Boolean(t.respuesta);
              const enEdicion = ticketEnEdicion === t.id;
              return (
                <Fragment key={t.id}>
                  <tr>
                    <td>
                      <div className="adm-fuerte">{t.usuarioNombre || "Usuario"}</div>
                      <div style={{ fontSize: "12px", color: "var(--adm-muted, #64748b)" }}>
                        {etiquetaRol(t.usuarioRol)}
                      </div>
                    </td>
                    <td style={{ whiteSpace: "nowrap" }}>{formatearFecha(t.creadoEn)}</td>
                    <td style={{ maxWidth: 360 }}>
                      {t.mensaje && t.mensaje.length > 110 ? `${t.mensaje.slice(0, 110)}…` : t.mensaje}
                    </td>
                    <td>
                      <span
                        className={`adm-chip ${
                          t.estado === "RESUELTO" ? "adm-chip--psicologo" : "adm-chip--aviso"
                        }`}
                      >
                        {t.estado === "RESUELTO" ? "Resuelto" : "Pendiente"}
                      </span>
                    </td>
                    <td>
                      <div className="adm-acciones">
                        <button
                          type="button"
                          className="adm-accion"
                          onClick={() => {
                            if (enEdicion) {
                              setTicketEnEdicion(null);
                              setTextoRespuesta("");
                            } else {
                              setTicketEnEdicion(t.id);
                              setTextoRespuesta(t.respuesta || "");
                            }
                          }}
                        >
                          {tieneRespuesta ? "Editar respuesta" : "Responder"}
                        </button>
                        {t.estado === "PENDIENTE" && !tieneRespuesta && (
                          <button
                            type="button"
                            className="adm-accion"
                            onClick={() => handleResolver(t.id)}
                          >
                            Marcar resuelto
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                  {enEdicion && (
                    <tr>
                      <td colSpan={5} style={{ background: "var(--adm-bg, #f8fafc)", padding: "16px" }}>
                        <form className="plan-form" onSubmit={(e) => handleResponder(e, t.id)} noValidate>
                          <label style={{ gridColumn: "1 / -1" }}>
                            {tieneRespuesta ? "Editar respuesta" : "Responder al usuario"}
                            <textarea
                              rows={3}
                              maxLength={2000}
                              value={textoRespuesta}
                              onChange={(e) => setTextoRespuesta(e.target.value)}
                              placeholder="Escribe la respuesta..."
                              style={{
                                padding: 10,
                                border: "1px solid var(--adm-line-2, #d5dce6)",
                                borderRadius: 8,
                                font: "inherit",
                                width: "100%",
                                boxSizing: "border-box",
                              }}
                              required
                            />
                          </label>
                          <div className="plan-form__acciones">
                            <button type="submit" className="adm-btn adm-btn--dorado" disabled={guardando}>
                              {guardando ? "Enviando..." : "Enviar"}
                            </button>
                            <button
                              type="button"
                              className="adm-btn adm-btn--borde"
                              onClick={() => {
                                setTicketEnEdicion(null);
                                setTextoRespuesta("");
                              }}
                              disabled={guardando}
                            >
                              Cancelar
                            </button>
                          </div>
                        </form>
                      </td>
                    </tr>
                  )}
                </Fragment>
              );
            })}
            {pag.items.length === 0 && (
              <tr>
                <td colSpan={5} className="adm-vacio">
                  No hay mensajes de soporte para este filtro.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <Paginador paginacion={pag} />
    </section>
  );
}