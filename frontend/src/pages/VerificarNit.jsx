import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import "../styles/app-shell.css";
import "../styles/Empresas.css";
import { request } from "../api/client";
import { formatearNit } from "../utils/validaciones";
import Toast from "../components/Toast";
import AppTopbar from "../components/AppTopbar";
import { useAuth } from "../context/AuthContext";

const MENSAJE_NIT_EXISTENTE = "La empresa con este NIT ya se encuentra registrada";
const ESPERA_REDIRECCION_MS = 3000;

export default function VerificarNit() {
  const navigate = useNavigate();
  const { usuario } = useAuth();
  const [nit, setNit] = useState("");
  const [tocados, setTocados] = useState({});
  const [intento, setIntento] = useState(false);

  const [error, setError] = useState("");
  const [verificando, setVerificando] = useState(false);
  const [nitYaRegistrado, setNitYaRegistrado] = useState(false);
  const temporizador = useRef(null);

  // Evita que el temporizador dispare una navegación si la persona sale de la página antes.
  useEffect(() => () => clearTimeout(temporizador.current), []);

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
    if (nitYaRegistrado) return;
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
        // NIT ya registrado: aviso (toast) y, a los 3 segundos, vuelta automática a inicio.
        setNitYaRegistrado(true);
        temporizador.current = setTimeout(() => {
          navigate("/Inicio", { replace: true });
        }, ESPERA_REDIRECCION_MS);
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
      {nitYaRegistrado && (
        <Toast mensaje={MENSAJE_NIT_EXISTENTE} tipo="info" duracion={ESPERA_REDIRECCION_MS} />
      )}

      {/* Con sesión: barra completa (logo -> /Inicio y perfil a la derecha).
          Sin sesión: solo el logo, que lleva a la página principal. */}
      {usuario ? (
        <AppTopbar />
      ) : (
        <header className="app-topbar">
          <Link to="/" aria-label="Ir a la página principal">
            <img src="/logo oscu.png" alt="Magnus SIG" className="app-topbar-logo" />
          </Link>
        </header>
      )}

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
                  disabled={nitYaRegistrado}
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

              <button type="submit" className="btn-primary" disabled={verificando || nitYaRegistrado}>
                {verificando ? "Verificando..." : "Continuar"}
              </button>
            </form>
          </div>
        </div>
      </main>
    </div>
  );
}