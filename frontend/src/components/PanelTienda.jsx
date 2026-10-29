import { useState } from "react";
import PanelPlanes from "./PanelPlanes";
import PanelProductos from "./PanelProductos";
import PanelHistorialCompras from "./PanelHistorialCompras";
import PanelVentasProductos from "./PanelVentasProductos";
import "../styles/PanelTienda.css";

const VISTAS = [
  { id: "planes", label: "Planes de baterías" },
  { id: "productos", label: "Productos" },
  { id: "historial", label: "Historial de compras" },
  { id: "ventas", label: "Panel de ventas" },
];

// Gestión de tienda: incluye planes, productos, historial de compras y panel de ventas.
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

      {vista === "planes" ? (
        <PanelPlanes />
      ) : vista === "productos" ? (
        <PanelProductos />
      ) : vista === "historial" ? (
        <PanelHistorialCompras />
      ) : (
        <PanelVentasProductos />
      )}
    </>
  );
}
