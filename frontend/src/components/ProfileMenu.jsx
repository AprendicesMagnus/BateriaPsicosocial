import { esSuperAdmin, etiquetaRol } from "../utils/roles";
import { urlArchivo } from "../api/client";
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "../styles/app-shell.css";

// Botón de perfil (foto o iniciales + nombre y rol) con menú desplegable.
// Compartido por AppTopbar y Dashboard.
export default function ProfileMenu() {
  const { usuario, cerrarSesion } = useAuth();
  const navigate = useNavigate();
  const [abierto, setAbierto] = useState(false);
  const menuRef = useRef(null);
  const botonRef = useRef(null);

  // Cierra el menú si se hace clic fuera de él.
  useEffect(() => {
    function handleClickFuera(e) {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setAbierto(false);
      }
    }
    document.addEventListener("mousedown", handleClickFuera);
    return () => document.removeEventListener("mousedown", handleClickFuera);
  }, []);

  // Cierra el menú con Escape y devuelve el foco al botón disparador.
  useEffect(() => {
    if (!abierto) return;
    function handleKeyDown(e) {
      if (e.key === "Escape") {
        e.preventDefault();
        setAbierto(false);
        botonRef.current?.focus();
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [abierto]);

  const nombreUsuario = usuario
    ? `${usuario.nombre ?? ""} ${usuario.apellido ?? ""}`.trim()
    : "Usuario";
  const rolUsuario = etiquetaRol(usuario?.rol);
  const iniciales =
    nombreUsuario
      .split(" ")
      .filter(Boolean)
      .slice(0, 2)
      .map((p) => p[0]?.toUpperCase())
      .join("") || "U";

  function handleVerPerfil() {
    setAbierto(false);
    navigate("/perfil");
  }

  function handleIrAlPanel() {
    setAbierto(false);
    navigate("/panel");
  }

  function handleIrASoporte() {
    setAbierto(false);
    navigate("/soporte");
  }

  function handleCerrarSesion() {
    setAbierto(false);
    cerrarSesion?.({ despues: () => navigate("/", { replace: true }) });
  }

  return (
    <div className="app-profile-menu" ref={menuRef}>
      <button
        ref={botonRef}
        type="button"
        className="app-profile"
        onClick={() => setAbierto((v) => !v)}
        aria-expanded={abierto}
        aria-controls="menu-perfil-dropdown"
        aria-label="Perfil de usuario"
      >
        {usuario?.fotoUrl ? (
          <img src={urlArchivo(usuario.fotoUrl)} alt={nombreUsuario} className="app-avatar app-avatar--foto" />
        ) : (
          <div className="app-avatar">{iniciales}</div>
        )}
        <div className="app-profile-text">
          <span className="app-profile-name">{nombreUsuario || "Usuario"}</span>
          {rolUsuario && <span className="app-profile-role">{rolUsuario}</span>}
        </div>
      </button>

      {abierto && (
        <div id="menu-perfil-dropdown" className="app-profile-dropdown">
          <button type="button" onClick={handleVerPerfil}>
            Ver perfil
          </button>
          {esSuperAdmin(usuario?.rol) && (
            <button type="button" onClick={handleIrAlPanel}>
              Panel De Administrador
            </button>
          )}
          <button type="button" onClick={handleIrASoporte}>
            Centro de ayuda
          </button>
          <button
            type="button"
            className="app-profile-dropdown-danger"
            onClick={handleCerrarSesion}
          >
            Cerrar sesión
          </button>
        </div>
      )}
    </div>
  );
}
