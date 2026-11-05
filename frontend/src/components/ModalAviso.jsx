import { useEffect, useRef } from "react";
import {
  BsExclamationTriangleFill,
  BsCheckCircleFill,
  BsInfoCircleFill,
} from "react-icons/bs";
import "../styles/ModalConfirmacion.css";

export default function ModalAviso({
  abierto,
  titulo,
  mensaje,
  textoBoton = "Entendido",
  tipo = "info",
  onCerrar,
}) {
  const botonRef = useRef(null);
  const elementoPrevioRef = useRef(null);

  useEffect(() => {
    if (!abierto) return;

    elementoPrevioRef.current = document.activeElement;

    const overflowOriginal = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const timer = setTimeout(() => {
      botonRef.current?.focus();
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
        e.preventDefault();
        onCerrar?.();
        return;
      }

      if (e.key === "Tab") {
        // Solo hay un elemento focusable: el botón. Atrapar el foco.
        e.preventDefault();
        botonRef.current?.focus();
      }
    }

    window.addEventListener("keydown", manejarKeyDown);
    return () => window.removeEventListener("keydown", manejarKeyDown);
  }, [abierto, onCerrar]);

  if (!abierto) return null;

  const claseIcono =
    tipo === "advertencia"
      ? "modal-confirmacion-icono-wrap--advertencia"
      : tipo === "exito"
      ? "modal-confirmacion-icono-wrap--exito"
      : "modal-confirmacion-icono-wrap--normal";

  const Icono =
    tipo === "advertencia"
      ? BsExclamationTriangleFill
      : tipo === "exito"
      ? BsCheckCircleFill
      : BsInfoCircleFill;

  return (
    <div
      className="modal-confirmacion-fondo"
      onClick={onCerrar}
    >
      <div
        className="modal-confirmacion-tarjeta"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="modal-aviso-titulo"
        aria-describedby="modal-aviso-mensaje"
        onClick={(e) => e.stopPropagation()}
      >
        <div
          className={`modal-confirmacion-icono-wrap ${claseIcono}`}
          aria-hidden="true"
        >
          <Icono size={22} />
        </div>

        <h3 id="modal-aviso-titulo" className="modal-confirmacion-titulo">
          {titulo}
        </h3>

        <div id="modal-aviso-mensaje" className="modal-confirmacion-mensaje">
          {mensaje}
        </div>

        <div className="modal-confirmacion-acciones modal-aviso-acciones">
          <button
            ref={botonRef}
            type="button"
            className="modal-confirmacion-btn-confirmar modal-confirmacion-btn-confirmar--normal"
            onClick={onCerrar}
          >
            {textoBoton}
          </button>
        </div>
      </div>
    </div>
  );
}
