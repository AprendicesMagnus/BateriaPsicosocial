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

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");

    const nitLimpio = nit.trim();
    if (!/^\d{9}$/.test(nitLimpio)) {
      setError("El NIT debe contener exactamente 9 dígitos numéricos.");
      return;
    }

    setVerificando(true);

    try {
      const res = await request(`/organizaciones/existe?nit=${nitLimpio}`);

      if (res.existe) {
        setError(
          "Ya existe una empresa registrada con este NIT. Si crees que es un error, inicia sesión o contacta a soporte."
        );
        return;
      }

      navigate("/crear-empresa", { state: { nit: nitLimpio } });
    } catch (err) {
      setError(err.message || "No se pudo verificar el NIT. Intenta de nuevo.");
    } finally {
      setVerificando(false);
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
          <div className="app-card empresas-card">
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
                  pattern="\d{9}"
                  minLength={9}
                  maxLength={9}
                  title="El NIT debe contener exactamente 9 dígitos numéricos"
                  placeholder="900123456"
                  value={nit}
                  onChange={(e) => setNit(e.target.value)}
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
          </div>
        </div>
      </main>
    </div>
  );
}