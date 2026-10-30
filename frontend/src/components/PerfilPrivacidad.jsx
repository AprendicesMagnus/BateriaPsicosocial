import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { descargarMisDatos, solicitarEliminacionCuenta } from "../api/perfil";
import "../styles/PerfilPrivacidad.css";

const MAX_MOTIVO = 500;

// Derechos del titular en el Perfil: descargar una copia de los datos propios y solicitar la
// eliminacion de la cuenta (la solicitud llega al Centro de ayuda del Super Administrador).
export default function PerfilPrivacidad({ token, puedeSolicitarEliminacion = true, onMensaje }) {
  const [descargando, setDescargando] = useState(false);
  const [error, setError] = useState("");
  const [modalAbierto, setModalAbierto] = useState(false);
  const [motivo, setMotivo] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [errorSolicitud, setErrorSolicitud] = useState("");
  const campoMotivo = useRef(null);
  const botonSolicitar = useRef(null);

  function abrirModal() {
    setErrorSolicitud("");
    setModalAbierto(true);
  }

  function cerrarModal() {
    setModalAbierto(false);
    setTimeout(() => botonSolicitar.current?.focus(), 0);
  }

  useEffect(() => {
    if (modalAbierto) campoMotivo.current?.focus();
  }, [modalAbierto]);

  useEffect(() => {
    if (!modalAbierto) return undefined;
    function alPresionarTecla(evento) {
      if (evento.key === "Escape" && !enviando) cerrarModal();
    }
    window.addEventListener("keydown", alPresionarTecla);
    return () => window.removeEventListener("keydown", alPresionarTecla);
  }, [modalAbierto, enviando]);

  async function handleDescargar() {
    setError("");
    setDescargando(true);
    try {
      await descargarMisDatos(token);
      onMensaje?.("Tus datos se descargaron correctamente.");
    } catch (err) {
      setError(err.message || "No se pudieron descargar tus datos.");
    } finally {
      setDescargando(false);
    }
  }

  async function handleSolicitar() {
    setErrorSolicitud("");
    setEnviando(true);
    try {
      const res = await solicitarEliminacionCuenta(token, motivo.trim());
      setMotivo("");
      cerrarModal();
      onMensaje?.(res?.message || "Tu solicitud de eliminación fue enviada.");
    } catch (err) {
      setErrorSolicitud(err.message || "No se pudo enviar la solicitud.");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <section className="perfil-privacidad" aria-labelledby="perfil-privacidad-titulo">
      <h3 id="perfil-privacidad-titulo" className="perfil-privacidad__titulo">
        Tus datos personales
      </h3>
      <p className="perfil-privacidad__texto">
        Descarga una copia de tus datos o solicita la eliminación de tu cuenta. Más información en la{" "}
        <Link
          to="/politica-de-datos"
          target="_blank"
          rel="noopener noreferrer"
          className="perfil-privacidad__enlace"
        >
          política de tratamiento de datos
        </Link>
        .
      </p>
      <div className="perfil-privacidad__acciones">
        <button type="button" className="app-btn-secondary" onClick={handleDescargar} disabled={descargando}>
          {descargando ? "Preparando..." : "Descargar mis datos"}
        </button>
        {puedeSolicitarEliminacion && (
          <button
            type="button"
            ref={botonSolicitar}
            className="app-btn-secondary perfil-privacidad__peligro"
            onClick={abrirModal}
          >
            Solicitar eliminación de mi cuenta
          </button>
        )}
      </div>
      {error && (
        <div className="perfil-error perfil-privacidad__error" role="alert">
          {error}
        </div>
      )}

      {modalAbierto && (
        <div className="perfil-modal__fondo">
          <div
            className="perfil-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="perfil-modal-titulo"
            aria-describedby="perfil-modal-descripcion"
          >
            <h2 id="perfil-modal-titulo" className="perfil-modal__titulo">
              Solicitar eliminación de mi cuenta
            </h2>
            <p id="perfil-modal-descripcion" className="perfil-modal__texto">
              Tu solicitud llegará al administrador de la plataforma por el Centro de ayuda y la atenderá según la
              política de tratamiento de datos. No se elimina nada de inmediato: algunos datos pueden conservarse
              durante el tiempo que exijan las normas aplicables.
            </p>
            <label htmlFor="motivo-eliminacion" className="perfil-modal__etiqueta">
              Motivo (opcional)
            </label>
            <textarea
              id="motivo-eliminacion"
              ref={campoMotivo}
              className="perfil-modal__campo"
              rows={4}
              maxLength={MAX_MOTIVO}
              value={motivo}
              onChange={(e) => setMotivo(e.target.value)}
              disabled={enviando}
            />
            <span className="perfil-modal__contador">
              {motivo.length}/{MAX_MOTIVO}
            </span>
            {errorSolicitud && (
              <div className="perfil-error" role="alert">
                {errorSolicitud}
              </div>
            )}
            <div className="perfil-modal__acciones">
              <button type="button" className="app-btn-secondary" onClick={cerrarModal} disabled={enviando}>
                Cancelar
              </button>
              <button
                type="button"
                className="perfil-modal__confirmar"
                onClick={handleSolicitar}
                disabled={enviando}
              >
                {enviando ? "Enviando..." : "Enviar solicitud"}
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
