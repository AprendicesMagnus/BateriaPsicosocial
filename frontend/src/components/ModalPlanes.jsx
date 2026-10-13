import { useEffect, useState } from "react";
import { fetchPlanes } from "../api/planes";
import { etiquetaRango, formatearPrecio } from "../utils/planes";
import "../styles/Planes.css";

// Ventana informativa con los planes de baterías (solo para consultar).
export default function ModalPlanes({ onCerrar }) {
  const [planes, setPlanes] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchPlanes()
      .then((lista) => setPlanes(lista || []))
      .catch(() => setError("No se pudieron cargar los planes. Intenta de nuevo."))
      .finally(() => setCargando(false));
  }, []);

  useEffect(() => {
    const alTeclear = (e) => e.key === "Escape" && onCerrar();
    window.addEventListener("keydown", alTeclear);
    return () => window.removeEventListener("keydown", alTeclear);
  }, [onCerrar]);

  return (
    <div className="planes-fondo" role="dialog" aria-modal="true" aria-labelledby="planes-titulo" onClick={onCerrar}>
      <div className="planes-modal" onClick={(e) => e.stopPropagation()}>
        <div className="planes-modal__cabecera">
          <div>
            <h2 id="planes-titulo">Planes</h2>
            <p>Precio por batería según la cantidad que necesites.</p>
          </div>
          <button type="button" className="planes-modal__cerrar" onClick={onCerrar} aria-label="Cerrar">
            ×
          </button>
        </div>

        {cargando && <p className="planes-vacio">Cargando planes...</p>}
        {error && <p className="planes-error">{error}</p>}
        {!cargando && !error && planes.length === 0 && <p className="planes-vacio">Pronto publicaremos nuestros planes.</p>}

        <div className="planes-grid">
          {planes.map((plan) => (
            <article className="plan-tarjeta" key={plan.id}>
              <span className="plan-tarjeta__rango">{etiquetaRango(plan.cantidadMin, plan.cantidadMax)}</span>
              <span className="plan-tarjeta__nombre">{plan.nombre}</span>
              <span className="plan-tarjeta__precio">{formatearPrecio(plan.precioUnitario)}</span>
              <span className="plan-tarjeta__nota">por batería</span>
            </article>
          ))}
        </div>
      </div>
    </div>
  );
}
