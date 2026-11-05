import { useEffect, useRef } from "react";
import { BsExclamationTriangleFill, BsInfoCircleFill } from "react-icons/bs";
import "../styles/ModalConfirmacion.css";

export default function ModalConfirmacion({
  abierto,
  titulo,
  mensaje,
  resumen,
  textoConfirmar = "Confirmar",
  textoCancelar = "Cancelar",
  tipo = "peligro",
  cargando = false,
  textoCargando,
  onConfirmar,
  onCancelar,
}) {
  const modalRef = useRef(null);
  const botonCancelarRef = useRef(null);
  const elementoPrevioRef = useRef(null);

  useEffect(() => {
    if (!abierto) return;

    elementoPrevioRef.current = document.activeElement;

    const overflowOriginal = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const timer = setTimeout(() => {
      botonCancelarRef.current?.focus();
    }, 10);

    return () => {
      clearTimeout(timer);
      document.body.style.overflow = overflowOriginal;
      if (
        elementoPrevioRef.current &&
        typeof elementoPrevioRef.current.focus === "function"
      ) {
        elementoPrevioRef.current.focus();
      }
    };
  }, [abierto]);

  useEffect(() => {
    if (!abierto) return;

    function manejarKeyDown(e) {
      if (e.key === "Escape") {
        if (!cargando && onCancelar) {
          e.preventDefault();
          onCancelar();
        }
        return;
      }

      if (e.key === "Tab") {
        const contenedor = modalRef.current;
        if (!contenedor) return;

        const elementos = contenedor.querySelectorAll(
          'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
        );
        if (!elementos.length) return;

        const primero = elementos[0];
        const ultimo = elementos[elementos.length - 1];

        if (e.shiftKey) {
          if (document.activeElement === primero) {
            e.preventDefault();
            ultimo.focus();
          }
        } else {
          if (document.activeElement === ultimo) {
            e.preventDefault();
            primero.focus();
          }
        }
      }
    }

    window.addEventListener("keydown", manejarKeyDown);
    return () => window.removeEventListener("keydown", manejarKeyDown);
  }, [abierto, cargando, onCancelar]);

  if (!abierto) return null;

  const esPeligro = tipo === "peligro";
  const textoBotonConfirmar = cargando
    ? textoCargando || (esPeligro ? "Cancelando..." : "Procesando...")
    : textoConfirmar;

  return (
    <div
      className="modal-confirmacion-fondo"
      onClick={() => {
        if (!cargando && onCancelar) onCancelar();
      }}
    >
      <div
        ref={modalRef}
        className="modal-confirmacion-tarjeta"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="modal-confirmacion-titulo"
        aria-describedby="modal-confirmacion-mensaje"
        onClick={(e) => e.stopPropagation()}
      >
        <div
          className={`modal-confirmacion-icono-wrap ${
            esPeligro
              ? "modal-confirmacion-icono-wrap--peligro"
              : "modal-confirmacion-icono-wrap--normal"
          }`}
          aria-hidden="true"
        >
          {esPeligro ? (
            <BsExclamationTriangleFill size={22} />
          ) : (
            <BsInfoCircleFill size={22} />
          )}
        </div>

        <h3 id="modal-confirmacion-titulo" className="modal-confirmacion-titulo">
          {titulo}
        </h3>

        <div id="modal-confirmacion-mensaje" className="modal-confirmacion-mensaje">
          {mensaje}
        </div>

        {resumen && (
          <div className="modal-confirmacion-resumen">
            {resumen}
          </div>
        )}

        <div className="modal-confirmacion-acciones">
          <button
            ref={botonCancelarRef}
            type="button"
            className="modal-confirmacion-btn-cancelar"
            onClick={onCancelar}
            disabled={cargando}
          >
            {textoCancelar}
          </button>
          <button
            type="button"
            className={`modal-confirmacion-btn-confirmar ${
              esPeligro
                ? "modal-confirmacion-btn-confirmar--peligro"
                : "modal-confirmacion-btn-confirmar--normal"
            }`}
            onClick={onConfirmar}
            disabled={cargando}
          >
            {textoBotonConfirmar}
          </button>
        </div>
      </div>
    </div>
  );
}
