import { useNavigate } from "react-router-dom";
import Logo from "../components/Logo";
import { useAuth } from "../context/AuthContext";

const ROL_LABEL = {
  ADMINISTRADOR: "Administrador",
  EVALUADOR_SST: "Evaluador SST",
  TRABAJADOR: "Trabajador",
};

export default function Panel() {
  const { usuario, cerrarSesion } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    cerrarSesion();
    navigate("/");
  }

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg-100)" }}>
      <header
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "18px 32px",
          background: "var(--white)",
          borderBottom: "1px solid var(--line-200)",
        }}
      >
        <Logo />
        <button className="btn-secondary" onClick={handleLogout}>
          Cerrar sesión
        </button>
      </header>

      <main style={{ maxWidth: 720, margin: "60px auto", padding: "0 24px" }}>
        <h1 style={{ color: "var(--ink-900)" }}>
          Bienvenido{usuario ? `, ${usuario.nombre}` : ""} 👋
        </h1>
        <p style={{ color: "var(--ink-500)" }}>
          Has iniciado sesión como{" "}
          <strong>{usuario ? ROL_LABEL[usuario.rol] || usuario.rol : "..."}</strong>. Este panel
          es un punto de partida: aquí se conectarán los módulos de aplicación de la Batería de
          Riesgo Psicosocial, evaluaciones, informes e indicadores descritos en el documento de
          requerimientos (RF07 - RF16).
        </p>
      </main>
    </div>
  );
}
