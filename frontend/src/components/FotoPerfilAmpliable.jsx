import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import "../styles/FotoPerfilAmpliable.css";

/** Imagen de perfil que permite abrir una vista ampliada, sin interferir
 * con los botones/menús que la contienen.
 */
export default function FotoPerfilAmpliable({ src, alt = "Foto de perfil", className = "" }) {
  const [abierta, setAbierta] = useState(false);

  useEffect(() => {
    if (!abierta) return undefined;

    const overflowAnterior = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const cerrarConEscape = (event) => {
      if (event.key === "Escape") setAbierta(false);
    };
    window.addEventListener("keydown", cerrarConEscape);

    return () => {
      document.body.style.overflow = overflowAnterior;
      window.removeEventListener("keydown", cerrarConEscape);
    };
  }, [abierta]);

  if (!src) return null;

  const abrir = (event) => {
    event.preventDefault();
    event.stopPropagation();
    setAbierta(true);
  };

  const cerrar = (event) => {
    event?.stopPropagation();
    setAbierta(false);
  };

  return (
    <>
      <img
        src={src}
        alt={alt}
        className={`foto-perfil-ampliable ${className}`.trim()}
        role="button"
        tabIndex={0}
        aria-label={`Ampliar ${alt.toLowerCase()}`}
        title="Ver foto ampliada"
        onClick={abrir}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") abrir(event);
          else if (event.key === "Escape") event.stopPropagation();
        }}
      />

      {abierta && createPortal(
        <div
          className="foto-perfil-lightbox"
          role="presentation"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) cerrar();
          }}
        >
          <section
            className="foto-perfil-lightbox__dialog"
            role="dialog"
            aria-modal="true"
            aria-label="Foto de perfil ampliada"
            onMouseDown={(event) => event.stopPropagation()}
          >
            <button
              type="button"
              className="foto-perfil-lightbox__close"
              onClick={cerrar}
              aria-label="Cerrar foto ampliada"
              autoFocus
            >
              <span aria-hidden="true">×</span>
            </button>
            <img src={src} alt={alt} className="foto-perfil-lightbox__image" />
          </section>
        </div>,
        document.body
      )}
    </>
  );
}
