import { useEffect, useRef, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function AppTopbar() {
  // Ajusta "cerrarSesion" si tu AuthContext la expone con otro nombre.
  const { usuario, cerrarSesion } = useAuth();
  const navigate = useNavigate();
  const [abierto, setAbierto] = useState(false);
  const menuRef = useRef(null);

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

  const nombreUsuario = usuario
    ? `${usuario.nombre ?? ""} ${usuario.apellido ?? ""}`.trim()
    : "Usuario";
  const rolUsuario = usuario?.rol ?? "";
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

  function handleCerrarSesion() {
    setAbierto(false);
    cerrarSesion?.();
    navigate("/iniciar-sesion");
  }

  return (
    <header className="app-topbar">
      <Link to="/" aria-label="Ir a la página principal" style={{ display: "inline-flex" }}>
        <img src="/logo oscu.png" alt="Magnus SIG" className="app-topbar-logo" style={{ cursor: "pointer" }} />
      </Link>

      <div className="app-profile-menu" ref={menuRef}>
        <button
          type="button"
          className="app-profile"
          onClick={() => setAbierto((v) => !v)}
          aria-haspopup="true"
          aria-expanded={abierto}
        >
          {/* ANTES: <div className="app-avatar">{iniciales}</div>
              Ahora: si usuario.fotoUrl existe, se muestra la foto; si no, las iniciales de siempre. */}
          {usuario?.fotoUrl ? (
            <img src={usuario.fotoUrl} alt={nombreUsuario} className="app-avatar app-avatar--foto" />
          ) : (
            <div className="app-avatar">{iniciales}</div>
          )}
          <div className="app-profile-text">
            <span className="app-profile-name">{nombreUsuario}</span>
            {rolUsuario && <span className="app-profile-role">{rolUsuario}</span>}
          </div>
        </button>

        {abierto && (
          <div className="app-profile-dropdown">
            <button type="button" onClick={handleVerPerfil}>
              Ver perfil
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
    </header>
  );
}