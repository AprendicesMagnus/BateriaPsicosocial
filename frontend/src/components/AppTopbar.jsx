import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { rutaInicial } from "../utils/roles";
import ProfileMenu from "./ProfileMenu";
import CampanaNotificaciones from "./CampanaNotificaciones";

export default function AppTopbar() {
  const { usuario } = useAuth();
  return (
    <header className="app-topbar">
      <Link to={rutaInicial(usuario?.rol)} aria-label="Ir al inicio" style={{ display: "inline-flex" }}>
        <img src="/logo oscu.png" alt="Magnus SIG" className="app-topbar-logo" style={{ cursor: "pointer" }} />
      </Link>

      <div className="app-acciones-usuario">
        <CampanaNotificaciones />
        <ProfileMenu />
      </div>
    </header>
  );
}
