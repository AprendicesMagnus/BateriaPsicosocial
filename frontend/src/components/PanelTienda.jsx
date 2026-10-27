import { useState } from "react";
import PanelPlanes from "./PanelPlanes";
import PanelProductos from "./PanelProductos";
import "../styles/PanelTienda.css";

const VISTAS = [
  { id: "planes", label: "Planes de baterías" },
  { id: "productos", label: "Productos" },
];

// Gestión de tienda: un solo apartado con selector entre Planes y Productos.
export default function PanelTienda() {
  const [vista, setVista] = useState("planes");

  return (
    <>
      <div className="tienda-selector" role="tablist" aria-label="Qué deseas gestionar">
        <span className="tienda-selector__titulo">Gestionar:</span>
        {VISTAS.map((v) => (
          <button
            key={v.id}
            type="button"
            role="tab"
            aria-selected={vista === v.id}
            className={`tienda-selector__op ${vista === v.id ? "activo" : ""}`}
            onClick={() => setVista(v.id)}
          >
            {v.label}
          </button>
        ))}
      </div>

      {vista === "planes" ? <PanelPlanes /> : <PanelProductos />}
    </>
  );
}
