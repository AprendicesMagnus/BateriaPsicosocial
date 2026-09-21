import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import "../styles/app-shell.css";
import "../styles/Empresas.css";
import { request } from "../api/client";
import { formatearNit } from "../utils/validaciones";

export default function VerificarNit() {
  const navigate = useNavigate();
  const [nit, setNit] = useState("");
  const [tocados, setTocados] = useState({});
  const [intento, setIntento] = useState(false);

  const [error, setError] = useState("");
  const [verificando, setVerificando] = useState(false);
  const [empresaEncontrada, setEmpresaEncontrada] = useState(null);

  const marcar = (campo) => {
    setTocados((prev) => ({ ...prev, [campo]: true }));
  };

  const errores = {
    nit: !nit
      ? "Este campo es obligatorio."
      : !/^\d{9}-\d$/.test(nit.trim())
      ? "El NIT debe estar en formato 900123456-7 (9 dígitos base, guion y dígito verificador)."
      : "",
  };

  const mostrarError = (campo) => Boolean((tocados[campo] || intento) && errores[campo]);

  async function handleSubmit(e) {
    if (e) e.preventDefault();
    setError("");
    setIntento(true);

    if (errores.nit) {
      setTimeout(() => {
        document.querySelector(".field__input--invalid")?.focus();
      }, 0);
      return;
    }

    const nitLimpio = nit.trim();
    setVerificando(true);

    try {
      const res = await request(`/organizaciones/existe?nit=${encodeURIComponent(nitLimpio)}`);

      if (res.existe) {
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
    setTocados({});
    setIntento(false);
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

                <form className="empresas-form" onSubmit={handleSubmit} noValidate>
                  <label className="field">
                    <span className="field__label">NIT de la empresa (con dígito verificador)</span>
                    <input
                      className={`field__input ${mostrarError("nit") ? "field__input--invalid" : ""}`}
                      aria-invalid={mostrarError("nit") ? "true" : "false"}
                      aria-describedby={mostrarError("nit") ? "nit-error" : undefined}
                      placeholder="900123456-7"
                      maxLength={11}
                      value={nit}
                      onChange={(e) => setNit(formatearNit(e.target.value))}
                      onBlur={() => marcar("nit")}
                    />
                    {mostrarError("nit") && (
                      <span className="field__error" id="nit-error">
                        {errores.nit}
                      </span>
                    )}
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