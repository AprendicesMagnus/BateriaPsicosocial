import { etiquetaRol } from "../utils/roles";
import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import AppTopbar from "../components/AppTopbar";
import "../styles/app-shell.css";
import "../styles/Perfil.css";
import { request } from "../api/client";

function formatearFecha(fechaIso) {
  if (!fechaIso) return "—";
  return new Intl.DateTimeFormat("es-CO", {
    day: "numeric",
    month: "long",
    year: "numeric",
  }).format(new Date(fechaIso));
}

function ReceiptIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path
        d="M6 3h12v18l-2.5-1.5L13 21l-2.5-1.5L8 21l-2-1.5V3Z"
        strokeLinejoin="round"
      />
      <path d="M9 8h6M9 12h6M9 16h3" strokeLinecap="round" />
    </svg>
  );
}

export default function Perfil() {
  const { usuario, token } = useAuth();
  const [compras, setCompras] = useState([]);
  const [loadingCompras, setLoadingCompras] = useState(false);
  const [errorCompras, setErrorCompras] = useState(null);

  useEffect(() => {
    if (usuario?.id && token) {
      setLoadingCompras(true);
      request(`/usuarios/${usuario.id}/compras`, { token })
        .then((data) => setCompras(data))
        .catch((err) => setErrorCompras(err.message))
        .finally(() => setLoadingCompras(false));
    }
  }, [usuario?.id, token]);

  const nombreUsuario = usuario
    ? `${usuario.nombre ?? ""} ${usuario.apellido ?? ""}`.trim()
    : "Usuario";
  const rolUsuario = etiquetaRol(usuario?.rol) || "Sin rol asignado";
  const correoUsuario = usuario?.email ?? usuario?.correo ?? "—";
  const empresaUsuario = usuario?.empresa ?? "—";
  const iniciales =
    nombreUsuario
      .split(" ")
      .filter(Boolean)
      .slice(0, 2)
      .map((p) => p[0]?.toUpperCase())
      .join("") || "U";

  return (
    <div className="app-shell-page">
      <AppTopbar />

      <main className="app-hero">
        <div className="app-decor app-decor--1" />
        <div className="app-decor app-decor--2" />
        <div className="app-decor app-decor--3" />

        <div className="app-content">
          <nav className="app-breadcrumb">
            Mi cuenta <span>›</span> Perfil
          </nav>
          <h1 className="app-title">Mi Perfil</h1>
          <p className="app-subtitle">Consulta y administra la información de tu cuenta.</p>

          <div className="perfil-layout">
            <div className="app-card perfil-card">
              <div className="perfil-header">
                {/* ANTES: <div className="perfil-avatar">{iniciales}</div>
                    Ahora: si usuario.fotoUrl existe, se muestra la foto; si no, las iniciales de siempre. */}
                {usuario?.fotoUrl ? (
                  <img
                    src={usuario.fotoUrl}
                    alt={nombreUsuario}
                    className="perfil-avatar perfil-avatar--foto"
                  />
                ) : (
                  <div className="perfil-avatar">{iniciales}</div>
                )}
                <div>
                  <h2 className="perfil-nombre">{nombreUsuario}</h2>
                  <span className="perfil-rol">{rolUsuario}</span>
                </div>
              </div>

              <div className="perfil-divider" />

              <div className="perfil-grid">
                <div className="perfil-field">
                  <span className="perfil-field-label">Nombre</span>
                  <span className="perfil-field-value">{usuario?.nombre ?? "—"}</span>
                </div>
                <div className="perfil-field">
                  <span className="perfil-field-label">Apellido</span>
                  <span className="perfil-field-value">{usuario?.apellido ?? "—"}</span>
                </div>
                <div className="perfil-field">
                  <span className="perfil-field-label">Correo electrónico</span>
                  <span className="perfil-field-value">{correoUsuario}</span>
                </div>
                <div className="perfil-field">
                  <span className="perfil-field-label">Rol</span>
                  <span className="perfil-field-value">{rolUsuario}</span>
                </div>
                <div className="perfil-field">
                  <span className="perfil-field-label">Empresa</span>
                  <span className="perfil-field-value">{empresaUsuario}</span>
                </div>
              </div>

              <div className="perfil-actions">
                <button type="button" className="app-btn-secondary" disabled title="Disponible próximamente">
                  Editar perfil
                </button>
                <button type="button" className="app-btn-secondary" disabled title="Disponible próximamente">
                  Cambiar contraseña
                </button>
              </div>
            </div>

            {/* ===================== HISTORIAL DE COMPRAS ===================== */}
            <div className="app-card compras-card">
              <h2 className="compras-titulo">Historial de compras</h2>
              <p className="compras-subtitulo">Baterías de riesgo psicosocial compradas</p>

              {loadingCompras && <p style={{ fontSize: "14px", color: "#64748b" }}>Cargando compras...</p>}
              {errorCompras && <p style={{ fontSize: "14px", color: "#b91c1c" }}>{errorCompras}</p>}

              {!loadingCompras && compras.length > 0 ? (
                <div className="compras-list">
                  {compras.map((compra) => (
                    <div className="compras-row" key={compra.id}>
                      <span className="compras-row-icon">
                        <ReceiptIcon />
                      </span>
                      <div className="compras-row-main">
                        <span className="compras-row-qty">
                          {compra.cantidad} {compra.cantidad === 1 ? "batería" : "baterías"} ({compra.estado})
                        </span>
                        <span className="compras-row-date">{formatearFecha(compra.fecha)}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : !loadingCompras && (
                <div className="compras-empty">
                  <p>Aún no has comprado ninguna batería.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}