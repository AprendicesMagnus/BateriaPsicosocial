import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import AppTopbar from "../components/AppTopbar";
import { useAuth } from "../context/AuthContext";
import { fetchMisEmpresas } from "../api/perfil";
import "../styles/app-shell.css";
import "../styles/MisEmpresas.css";

function formatearFecha(fechaIso) {
  if (!fechaIso) return "—";
  return new Intl.DateTimeFormat("es-CO", { day: "numeric", month: "long", year: "numeric" }).format(
    new Date(fechaIso)
  );
}

export default function MisEmpresas() {
  const { token } = useAuth();
  const location = useLocation();
  const mensajeInicial = location.state?.mensaje ?? "";

  const [empresas, setEmpresas] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;
    fetchMisEmpresas(token)
      .then(setEmpresas)
      .catch((err) => setError(err.message || "No se pudieron cargar tus empresas."))
      .finally(() => setCargando(false));
  }, [token]);

  return (
    <div className="app-shell-page">
      <AppTopbar />

      <main className="app-hero">
        <div className="app-decor app-decor--1" />
        <div className="app-decor app-decor--2" />
        <div className="app-decor app-decor--3" />

        <div className="app-content">
          <nav className="app-breadcrumb">
            Empresas <span>›</span> Mis empresas
          </nav>
          <h1 className="app-title">Mis Empresas</h1>
          <p className="app-subtitle">Empresas que has registrado con tu cuenta.</p>

          {mensajeInicial && <div className="mis-empresas-ok">{mensajeInicial}</div>}
          {error && <div className="mis-empresas-error">{error}</div>}

          <div className="app-card mis-empresas-card">
            {cargando ? (
              <p className="mis-empresas-vacio">Cargando empresas...</p>
            ) : empresas.length === 0 ? (
              <div className="mis-empresas-vacio">
                <p>Todavía no has creado ninguna empresa.</p>
                <Link to="/verificar-nit" className="btn-primary mis-empresas-btn">
                  Crear empresa
                </Link>
              </div>
            ) : (
              <div className="mis-empresas-tabla-wrap">
                <table className="mis-empresas-tabla">
                  <thead>
                    <tr>
                      <th>Razón social</th>
                      <th>NIT</th>
                      <th>Sector</th>
                      <th>Ciudad</th>
                      <th>Creada</th>
                    </tr>
                  </thead>
                  <tbody>
                    {empresas.map((empresa) => (
                      <tr key={empresa.id}>
                        <td>{empresa.nombre}</td>
                        <td>{empresa.nit}</td>
                        <td>{empresa.sector ?? "—"}</td>
                        <td>{empresa.municipio ?? "—"}</td>
                        <td>{formatearFecha(empresa.creadoEn)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
