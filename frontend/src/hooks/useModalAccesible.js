import { useEffect, useRef } from "react";

const SELECTOR_ENFOCABLES =
  'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

export default function useModalAccesible(
  abierto,
  contenedorRef,
  { onCerrar, cerrarConEsc = true } = {}
) {
  const elementoPrevioRef = useRef(null);

  useEffect(() => {
    if (!abierto) return;

    elementoPrevioRef.current = document.activeElement;
    const overflowOriginal = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const timer = setTimeout(() => {
      const contenedor = contenedorRef.current;
      if (!contenedor) return;
      const autoF =
        contenedor.querySelector("[autofocus], [data-autofocus]") ||
        contenedor.querySelectorAll(SELECTOR_ENFOCABLES)[0];
      if (autoF) autoF.focus();
    }, 10);

    return () => {
      clearTimeout(timer);
      document.body.style.overflow = overflowOriginal;
      const prev = elementoPrevioRef.current;
      if (prev && typeof prev.focus === "function" && document.contains(prev)) {
        prev.focus();
      }
    };
  }, [abierto]);

  useEffect(() => {
    if (!abierto) return;

    function manejarKeyDown(e) {
      if (e.key === "Escape") {
        if (cerrarConEsc && onCerrar) {
          e.preventDefault();
          onCerrar();
        }
        return;
      }
      if (e.key === "Tab") {
        const contenedor = contenedorRef.current;
        if (!contenedor) return;
        const elementos = Array.from(
          contenedor.querySelectorAll(SELECTOR_ENFOCABLES)
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
  }, [abierto, cerrarConEsc, onCerrar]);
}
