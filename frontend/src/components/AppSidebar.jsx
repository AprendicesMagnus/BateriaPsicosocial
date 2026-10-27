import { useState } from "react";
import "../styles/AppSidebar.css";

/**
 * Sidebar compartido (Dashboard y Panel).
 * items: [{ key, label, icono?, activo?, onClick }]
 * En pantallas <= 860px el menú se colapsa tras un botón ☰.
 */
export default function AppSidebar({ items, onLogoClick, mostrarPie = false, acciones = null }) {
  const [abierto, setAbierto] = useState(false);

  return (
    <aside className="sidebar">
      <div
        className="sidebar__logo"
        onClick={onLogoClick}
        style={{ cursor: "pointer" }}
        role="button"
        aria-label="Ir al inicio"
      >
        <img src="/logob1.png" alt="Magnus" style={{ height: 70, marginRight: "auto" }} />
      </div>

      <button
        type="button"
        className="sidebar__burger"
        aria-label={abierto ? "Cerrar menú" : "Abrir menú"}
        aria-expanded={abierto}
        onClick={() => setAbierto((v) => !v)}
      >
        {abierto ? "✕" : "☰"}
      </button>

      <nav className={`sidebar__menu ${abierto ? "sidebar__menu--abierto" : ""}`}>
        {items.map((it) => (
          <button
            key={it.key}
            className={`menu-item ${it.activo ? "active" : ""}`}
            type="button"
            onClick={() => {
              setAbierto(false);
              it.onClick();
            }}
          >
            {it.icono && <span>{it.icono}</span>}
            {it.label}
          </button>
        ))}
      </nav>

      {acciones && <div className="sidebar__acciones">{acciones}</div>}

      {mostrarPie && (
        <div className="sidebar__footer">
          <div className="footer-icon">◇</div>
          <span>
            Tu bienestar también
            <br />
            es parte del trabajo
          </span>
        </div>
      )}
    </aside>
  );
}
