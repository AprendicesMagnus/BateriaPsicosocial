import { Link } from "react-router-dom";
import ProfileMenu from "./ProfileMenu";

export default function AppTopbar() {
  return (
    <header className="app-topbar">
      <Link to="/Inicio" aria-label="Ir al inicio" style={{ display: "inline-flex" }}>
        <img src="/logo oscu.png" alt="Magnus SIG" className="app-topbar-logo" style={{ cursor: "pointer" }} />
      </Link>

      <ProfileMenu />
    </header>
  );
}
