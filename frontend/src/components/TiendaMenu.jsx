import { useEffect, useRef, useState } from "react";
import "../styles/Catalogo.css";

/**
 * Menú desplegable "Tienda" (barra superior de escritorio).
 * Opciones: Planes y Catálogo de Productos.
 */
export default function TiendaMenu({ onPlanes, onCatalogo, icono = null, peso = 700 }) {
  const [abierto, setAbierto] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const alClicFuera = (e) => ref.current && !ref.current.contains(e.target) && setAbierto(false);
    const alTeclear = (e) => e.key === "Escape" && setAbierto(false);
    document.addEventListener("mousedown", alClicFuera);
    document.addEventListener("keydown", alTeclear);
    return () => {
      document.removeEventListener("mousedown", alClicFuera);
      document.removeEventListener("keydown", alTeclear);
    };
  }, []);

  const elegir = (accion) => () => {
    setAbierto(false);
    accion();
  };

  return (
    <div className="tienda-dd" ref={ref}>
      <button
        type="button"
        className="tienda-dd__trigger"
        style={{ fontWeight: peso }}
        aria-haspopup="true"
        aria-expanded={abierto}
        onClick={() => setAbierto((v) => !v)}
      >
        {icono}
        Tienda
        <span className="tienda-dd__flecha" aria-hidden="true">{abierto ? "▴" : "▾"}</span>
      </button>

      {abierto && (
        <div className="tienda-dd__menu" role="menu">
          <button type="button" role="menuitem" onClick={elegir(onPlanes)}>Planes</button>
          <button type="button" role="menuitem" onClick={elegir(onCatalogo)}>Catálogo de Productos</button>
        </div>
      )}
    </div>
  );
}
