import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import "../styles/app-shell.css";
import "../styles/Empresas.css";
import { request } from "../api/client";

const SECTORES = ["Agropecuario", "Energético", "Turístico", "Comercial", "Otro"];

export default function CrearEmpresa() {
  const location = useLocation();
  const navigate = useNavigate();

  const nit = location.state?.nit;

  useEffect(() => {
    if (!nit) {
      navigate("/verificar-nit", { replace: true });
    }
  }, [nit, navigate]);

  const [razonSocial, setRazonSocial] = useState("");
  const [codigoVerificacion, setCodigoVerificacion] = useState("");
  const [sector, setSector] = useState("");
  const [numeroTrabajadores, setNumeroTrabajadores] = useState("");
  const [ciudad, setCiudad] = useState("");
  const [correoContacto, setCorreoContacto] = useState("");

  const [usuarioNombre, setUsuarioNombre] = useState("");
  const [usuarioApellido, setUsuarioApellido] = useState("");
  const [usuarioEmail, setUsuarioEmail] = useState("");
  const [usuarioPassword, setUsuarioPassword] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  if (!nit) return null;

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await request("/organizaciones/autorregistro", {
        method: "POST",
        body: {
          nit,
          nombre: razonSocial,
          codigoVerificacion,
          sector,
          numeroTrabajadores: parseInt(numeroTrabajadores, 10) || null,
          municipio: ciudad,
          email: correoContacto,
          usuarioNombre,
          usuarioApellido,
          usuarioEmail,
          usuarioPassword,
        },
      });

      navigate("/verificar-cuenta", {
        state: { email: usuarioEmail },
      });
    } catch (err) {
      setError(err.message || "No se pudo crear la empresa.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app-shell-page">
      <header className="app-topbar">
        <Link to="/" aria-label="Ir a la página principal">
          <img src="/logo oscu.png" alt="Magnus SIG" className="app-topbar-logo" />
        </Link>
      </header>

      <main className="app-hero">
        <div className="app-decor app-decor--1" />
        <div className="app-decor app-decor--2" />
        <div className="app-decor app-decor--3" />

        <div className="empresas-center">
          <div className="app-card empresas-card empresas-card--ancho">
            <div className="empresas-title-row">
              <h1 className="empresas-titulo">Crear empresa y usuario responsable</h1>
              <span className="empresas-badge">Empresa no registrada</span>
            </div>
            <p className="empresas-subtitulo">
              NIT verificado: <strong>{nit}</strong>. Registra los datos de tu empresa y el primer usuario Evaluador SST responsable.
            </p>

            <form className="empresas-form" onSubmit={handleSubmit}>
              <h3 style={{ fontSize: "16px", color: "var(--ink-900, #12314b)", margin: "8px 0 4px" }}>
                Datos de la Empresa
              </h3>

              <label className="field">
                <span className="field__label">Razón social</span>
                <input
                  className="field__input"
                  placeholder="Nombre de la empresa"
                  value={razonSocial}
                  onChange={(e) => setRazonSocial(e.target.value)}
                  required
                />
              </label>

              <label className="field">
                <span className="field__label">Código de verificación</span>
                <input
                  className="field__input"
                  placeholder="Ej. 112209393"
                  inputMode="numeric"
                  value={codigoVerificacion}
                  onChange={(e) => setCodigoVerificacion(e.target.value.replace(/\D/g, ""))}
                  required
                />
              </label>

              <div className="empresas-form-row">
                <label className="field">
                  <span className="field__label">Sector económico</span>
                  <select
                    className="field__input"
                    value={sector}
                    onChange={(e) => setSector(e.target.value)}
                    required
                  >
                    <option value="" disabled>
                      Selecciona un sector
                    </option>
                    {SECTORES.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="field">
                  <span className="field__label">N.º de trabajadores</span>
                  <input
                    className="field__input"
                    type="number"
                    min="1"
                    placeholder="Ej. 40"
                    value={numeroTrabajadores}
                    onChange={(e) => setNumeroTrabajadores(e.target.value)}
                    required
                  />
                </label>
              </div>

              <div className="empresas-form-row">
                <label className="field">
                  <span className="field__label">Ciudad / Municipio</span>
                  <input
                    className="field__input"
                    placeholder="Ej. Neiva"
                    value={ciudad}
                    onChange={(e) => setCiudad(e.target.value)}
                    required
                  />
                </label>

                <label className="field">
                  <span className="field__label">Correo institucional de la empresa</span>
                  <input
                    className="field__input"
                    type="email"
                    placeholder="contacto@empresa.com"
                    value={correoContacto}
                    onChange={(e) => setCorreoContacto(e.target.value)}
                    required
                  />
                </label>
              </div>

              <hr style={{ border: "none", borderTop: "1px solid #e2e8f0", margin: "16px 0" }} />

              <h3 style={{ fontSize: "16px", color: "var(--ink-900, #12314b)", margin: "4px 0 4px" }}>
                Datos del Usuario Evaluador SST (Responsable)
              </h3>

              <div className="empresas-form-row">
                <label className="field">
                  <span className="field__label">Nombre del responsable</span>
                  <input
                    className="field__input"
                    placeholder="Ej. Carlos"
                    value={usuarioNombre}
                    onChange={(e) => setUsuarioNombre(e.target.value)}
                    required
                  />
                </label>

                <label className="field">
                  <span className="field__label">Apellido del responsable</span>
                  <input
                    className="field__input"
                    placeholder="Ej. Rodríguez"
                    value={usuarioApellido}
                    onChange={(e) => setUsuarioApellido(e.target.value)}
                    required
                  />
                </label>
              </div>

              <div className="empresas-form-row">
                <label className="field">
                  <span className="field__label">Correo personal del usuario</span>
                  <input
                    className="field__input"
                    type="email"
                    placeholder="carlos.rodriguez@empresa.com"
                    value={usuarioEmail}
                    onChange={(e) => setUsuarioEmail(e.target.value)}
                    required
                  />
                </label>

                <label className="field">
                  <span className="field__label">Contraseña (mín. 8 caracteres, números y mayúsculas)</span>
                  <input
                    className="field__input"
                    type="password"
                    placeholder="••••••••"
                    value={usuarioPassword}
                    onChange={(e) => setUsuarioPassword(e.target.value)}
                    required
                  />
                </label>
              </div>

              {error && <div className="form-message form-message--error">{error}</div>}

              <button type="submit" className="btn-primary" disabled={loading}>
                {loading ? "Registrando empresa y usuario..." : "Registrar empresa y continuar"}
              </button>
            </form>
          </div>
        </div>
      </main>
    </div>
  );
}