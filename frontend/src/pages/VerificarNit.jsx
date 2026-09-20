import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import "../styles/app-shell.css";
import "../styles/empresas.css";
import { request } from "../api/client";

export default function VerificarNit() {
  const navigate = useNavigate();
  const [nit, setNit] = useState("");
  const [error, setError] = useState("");
  const [verificando, setVerificando] = useState(false);
  const [empresaEncontrada, setEmpresaEncontrada] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");

    const nitLimpio = nit.replace(/\D/g, "");
    if (nitLimpio.length !== 9) {
      setError("El NIT debe tener exactamente 9 dígitos.");
      return;
    }

    setVerificando(true);

    try {
      const res = await request(`/organizaciones/existe?nit=${nitLimpio}`);

      if (res.existe) {
        // Ajusta estos campos si tu backend devuelve la empresa con otra forma.
        setEmpresaEncontrada(res.empresa ?? { nit: nitLimpio });
        return;
      }

      navigate("/crear-empresa", { state: { nit: nitLimpio } });
    } catch (err) {
  setError(err.message || "No se pudo verificar el NIT. Intenta de nuevo.");
} finally {
      setVerificando(false);
    }
  }

  function handleVerificarOtro() {
    setEmpresaEncontrada(null);
    setNit("");
    setError("");
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
          <div className="app-card empresas-card">
            {empresaEncontrada ? (
              <>
                <h1 className="empresas-titulo">Empresa encontrada</h1>
                <p className="empresas-subtitulo">
                  Ya existe una empresa registrada con este NIT.
                </p>

                <div className="empresas-info-box">
                  <div className="empresas-info-row">
                    <span className="empresas-info-label">Empresa</span>
                    <span className="empresas-info-value">
                      {empresaEncontrada.nombre ?? "—"}
                    </span>
                  </div>
                  <div className="empresas-info-row">
                    <span className="empresas-info-label">NIT</span>
                    <span className="empresas-info-value">
                      {empresaEncontrada.nit ?? nit}
                    </span>
                  </div>
                  {empresaEncontrada.sector && (
                    <div className="empresas-info-row">
                      <span className="empresas-info-label">Sector</span>
                      <span className="empresas-info-value">{empresaEncontrada.sector}</span>
                    </div>
                  )}
                </div>

                <Link to="/iniciar-sesion" className="btn-primary empresas-btn-link">
                  Iniciar sesión
                </Link>

                <button
                  type="button"
                  className="link-accent empresas-otro-nit"
                  onClick={handleVerificarOtro}
                >
                  Verificar otro NIT
                </button>
              </>
            ) : (
              <>
                <h1 className="empresas-titulo">Verificar NIT</h1>
                <p className="empresas-subtitulo">
                  Antes de crear tu empresa, verifiquemos que no esté registrada todavía.
                </p>

                <form className="empresas-form" onSubmit={handleSubmit}>
                  <label className="field">
                    <span className="field__label">NIT de la empresa</span>
                    <input
                      className="field__input"
                      inputMode="numeric"
                      placeholder="900123456"
                      maxLength={9}
                      value={nit}
                      onChange={(e) => setNit(e.target.value.replace(/\D/g, "").slice(0, 9))}
                      required
                    />
                  </label>

                  {error && <div className="form-message form-message--error">{error}</div>}

                  <button type="submit" className="btn-primary" disabled={verificando}>
                    {verificando ? "Verificando..." : "Continuar"}
                  </button>
                </form>

                <p className="empresas-nota">
                  ¿Tu empresa ya está registrada?{" "}
                  <Link className="link-accent" to="/iniciar-sesion">
                    Inicia sesión
                  </Link>
                </p>
              </>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}