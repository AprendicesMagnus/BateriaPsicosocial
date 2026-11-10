import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import "../styles/app-shell.css";
import "../styles/Empresas.css";
import "../styles/VerificarNit.css";
import { HiArrowRight, HiOutlineCheckCircle, HiOutlineInformationCircle, HiOutlineOfficeBuilding } from "react-icons/hi";
import { request } from "../api/client";
import { formatearNit } from "../utils/validaciones";
import Toast from "../components/Toast";
import AppTopbar from "../components/AppTopbar";
import BotonRegresar from "../components/BotonRegresar";
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
      : !/^\d{9,10}-\d$/.test(nit.trim())
      ? "El NIT debe tener 9 o 10 dígitos base, guion y dígito verificador."
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

      <main id="contenido-principal" tabIndex={-1} className="app-hero">
        <div className="app-decor app-decor--1" />
        <div className="app-decor app-decor--2" />
        <div className="app-decor app-decor--3" />

        <div className="empresas-center">
          <div className="app-card empresas-card nit-card">
            <BotonRegresar tono="oscuro" />

            <ol className="nit-pasos" aria-label="Progreso para registrar la empresa">
              <li className="nit-paso nit-paso--activo" aria-current="step">
                <span className="nit-paso__num">1</span>
                <span className="nit-paso__txt">Verificar NIT</span>
              </li>
              <li className="nit-paso__linea" aria-hidden="true" />
              <li className="nit-paso">
                <span className="nit-paso__num">2</span>
                <span className="nit-paso__txt">Datos de la empresa</span>
              </li>
            </ol>

            <div className="nit-encabezado">
              <span className="nit-icono" aria-hidden="true">
                <HiOutlineOfficeBuilding size={30} />
              </span>
              <h1 className="nit-titulo">Verificar NIT</h1>
              <p className="nit-subtitulo">
                Antes de crear tu empresa, verifiquemos que no esté registrada todavía.
              </p>
            </div>

            <form className="nit-form" onSubmit={handleSubmit} noValidate>
              <label className="field">
                <span className="field__label">NIT de la empresa (con dígito verificador)</span>
                <span className="nit-input">
                  <input
                    className={`field__input ${mostrarError("nit") ? "field__input--invalid" : ""}`}
                    aria-invalid={mostrarError("nit") ? "true" : "false"}
                    aria-describedby={mostrarError("nit") ? "nit-error" : "nit-ayuda"}
                    placeholder="900123456-7"
                    inputMode="numeric"
                    autoComplete="off"
                    maxLength={12}
                    value={nit}
                    disabled={nitYaRegistrado}
                    onChange={(e) => setNit(formatearNit(e.target.value))}
                    onBlur={() => marcar("nit")}
                  />
                  {nit && !errores.nit && (
                    <HiOutlineCheckCircle className="nit-input__ok" size={22} aria-label="Formato válido" />
                  )}
                </span>
                {mostrarError("nit") ? (
                  <span className="field__error" id="nit-error">
                    {errores.nit}
                  </span>
                ) : (
                  <span className="nit-ayuda" id="nit-ayuda">
                    Escríbelo sin puntos: 9 o 10 dígitos, guion y dígito verificador.
                  </span>
                )}
              </label>

              <div className="nit-info">
                <HiOutlineInformationCircle size={20} aria-hidden="true" />
                <p>
                  Cada empresa se registra una sola vez. Si el NIT ya existe, te avisaremos y volverás al inicio.
                </p>
              </div>

              {error && <div className="form-message form-message--error">{error}</div>}

              <button type="submit" className="btn-primary nit-btn" disabled={verificando || nitYaRegistrado}>
                {verificando ? "Verificando..." : (<>Continuar <HiArrowRight size={18} aria-hidden="true" /></>)}
              </button>
            </form>
          </div>
        </div>
      </main>
    </div>
  );
}