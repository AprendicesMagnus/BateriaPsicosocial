import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import "../styles/app-shell.css";
import "../styles/empresas.css";

// ==================================================
// Datos de ejemplo — reemplaza por tu API real cuando exista
// ==================================================
// Cuando haya backend, esto debería ser algo como:
//   const { data } = await api.get(`/empresas/existe?nit=${nit}`)
// Mientras tanto, se simula con una lista local de NITs ya "registrados".
const NITS_REGISTRADOS_MOCK = ["900123456", "901234567", "800555444"];

export default function VerificarNit() {
  const navigate = useNavigate();
  const [nit, setNit] = useState("");
  const [error, setError] = useState("");
  const [verificando, setVerificando] = useState(false);

  function handleSubmit(e) {
    e.preventDefault();
    setError("");

    const nitLimpio = nit.replace(/\D/g, "");
    if (nitLimpio.length < 9) {
      setError("Ingresa un NIT válido.");
      return;
    }

    setVerificando(true);

    // TODO: reemplazar por la verificación real contra el backend.
    setTimeout(() => {
      setVerificando(false);
      const yaExiste = NITS_REGISTRADOS_MOCK.includes(nitLimpio);

      if (yaExiste) {
        setError(
          "Ya existe una empresa registrada con este NIT. Si crees que es un error, inicia sesión o contacta a soporte."
        );
        return;
      }

      navigate("/crear-empresa", { state: { nit: nitLimpio } });
    }, 500);
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