import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import "../styles/app-shell.css";
import "../styles/empresas.css";

const SECTORES = ["Agropecuario", "Energético", "Turístico", "Comercial", "Otro"];

export default function CrearEmpresa() {
  const location = useLocation();
  const navigate = useNavigate();

  // El NIT llega desde VerificarNit.jsx (navigate con state).
  // Si alguien entra directo a esta URL sin pasar por ahí, lo mandamos de vuelta.
  const nit = location.state?.nit;

  useEffect(() => {
    if (!nit) {
      navigate("/verificar-nit", { replace: true });
    }
  }, [nit, navigate]);

  const [razonSocial, setRazonSocial] = useState("");
  const [sector, setSector] = useState("");
  const [numeroTrabajadores, setNumeroTrabajadores] = useState("");
  const [ciudad, setCiudad] = useState("");
  const [correoContacto, setCorreoContacto] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  if (!nit) return null; // evita el parpadeo del formulario mientras redirige

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      // ==================================================
      // TODO: conectar con el endpoint real de creación de empresas.
      // Lo que se enviaría: { nit, razonSocial, sector, numeroTrabajadores, ciudad, correoContacto }
      //
      // A propósito este formulario solo pide lo básico para identificar
      // la empresa. Cosas como dirección detallada, logo, usuarios
      // adicionales o los módulos habilitados se configuran después,
      // desde la ficha de la empresa ya creada — no hace falta pedirlas
      // todas de una vez aquí.
      // ==================================================
      await new Promise((resolve) => setTimeout(resolve, 800));

      navigate("/iniciar-sesion", {
        state: { message: "Empresa creada correctamente. Ahora puedes iniciar sesión para continuar." },
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
            <h1 className="empresas-titulo">Crear empresa</h1>
            <p className="empresas-subtitulo">
              NIT verificado: <strong>{nit}</strong>. Completa los datos básicos para registrar tu
              empresa — el resto lo puedes ajustar después.
            </p>

            <form className="empresas-form" onSubmit={handleSubmit}>
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

              <label className="field">
                <span className="field__label">Ciudad</span>
                <input
                  className="field__input"
                  placeholder="Ej. Neiva"
                  value={ciudad}
                  onChange={(e) => setCiudad(e.target.value)}
                  required
                />
              </label>

              <label className="field">
                <span className="field__label">Correo de contacto</span>
                <input
                  className="field__input"
                  type="email"
                  placeholder="contacto@empresa.com"
                  value={correoContacto}
                  onChange={(e) => setCorreoContacto(e.target.value)}
                  required
                />
              </label>

              {error && <div className="form-message form-message--error">{error}</div>}

              <button type="submit" className="btn-primary" disabled={loading}>
                {loading ? "Creando empresa..." : "Crear empresa"}
              </button>
            </form>
          </div>
        </div>
      </main>
    </div>
  );
}