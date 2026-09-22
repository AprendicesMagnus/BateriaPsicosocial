import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import "../styles/app-shell.css";
import "../styles/Empresas.css";
import { request } from "../api/client";
import {
  TEXTO_AYUDA_PASSWORD,
  emailValido,
  enteroEnRango,
  filtrarLugar,
  formatearNit,
  filtrarNombrePersona,
  filtrarTextoLibre,
  lugarValido,
  nombrePersonaValido,
  normalizarEmail,
  passwordValida,
  soloDigitos,
  textoLibreValido,
} from "../utils/validaciones";

const SECTORES = ["Agropecuario", "Energético", "Turístico", "Comercial", "Otro"];

export default function CrearEmpresa() {
  const location = useLocation();
  const navigate = useNavigate();

  const nitInicial = location.state?.nit;

  useEffect(() => {
    if (!nitInicial) {
      navigate("/verificar-nit", { replace: true });
    }
  }, [nitInicial, navigate]);

  const [razonSocial, setRazonSocial] = useState("");
  const [nit, setNit] = useState(nitInicial ?? "");
  const [codigoVerificacion, setCodigoVerificacion] = useState("");
  const [sector, setSector] = useState("");
  const [numeroTrabajadores, setNumeroTrabajadores] = useState("");
  const [ciudad, setCiudad] = useState("");
  const [correoContacto, setCorreoContacto] = useState("");

  const [usuarioNombre, setUsuarioNombre] = useState("");
  const [usuarioApellido, setUsuarioApellido] = useState("");
  const [usuarioEmail, setUsuarioEmail] = useState("");
  const [usuarioPassword, setUsuarioPassword] = useState("");

  const [tocados, setTocados] = useState({});
  const [intento, setIntento] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  if (!nitInicial) return null;

  const marcar = (campo) => {
    setTocados((prev) => ({ ...prev, [campo]: true }));
  };

  const dvEsperado = nit.includes("-") ? nit.split("-")[1] : "";
  const codVerValido = /^\d$/.test(codigoVerificacion) && (!dvEsperado || codigoVerificacion === dvEsperado);

  const errores = {
    razonSocial: !razonSocial
      ? "Este campo es obligatorio."
      : !textoLibreValido(razonSocial.trim(), 180)
      ? "La razón social debe tener al menos 2 letras y solo puede incluir letras, números y . , & ' ( ) / -"
      : "",
    nit: !nit
      ? "Este campo es obligatorio."
      : !/^\d{9}-\d$/.test(nit.trim())
      ? "El NIT debe estar en formato 900123456-7 (9 dígitos base, guion y dígito verificador)."
      : "",
    codigoVerificacion: !codigoVerificacion
      ? "Este campo es obligatorio."
      : !codVerValido
      ? "El código de verificación debe ser un solo dígito y coincidir con el del NIT."
      : "",
    sector: !sector ? "Selecciona una opción." : "",
    numeroTrabajadores: !numeroTrabajadores
      ? "Este campo es obligatorio."
      : !enteroEnRango(numeroTrabajadores, 1, 1000000)
      ? "Ingresa un número entero entre 1 y 1.000.000."
      : "",
    ciudad: !ciudad
      ? "Este campo es obligatorio."
      : !lugarValido(ciudad.trim())
      ? "Solo letras, espacios, punto y guion (entre 2 y 80 caracteres)."
      : "",
    correoContacto: !correoContacto
      ? "Este campo es obligatorio."
      : !emailValido(normalizarEmail(correoContacto))
      ? "Ingresa un correo válido."
      : "",
    usuarioNombre: !usuarioNombre
      ? "Este campo es obligatorio."
      : !nombrePersonaValido(usuarioNombre.trim(), 100)
      ? "Solo letras y espacios (mínimo 2 caracteres)."
      : "",
    usuarioApellido: !usuarioApellido
      ? "Este campo es obligatorio."
      : !nombrePersonaValido(usuarioApellido.trim(), 100)
      ? "Solo letras y espacios (mínimo 2 caracteres)."
      : "",
    usuarioEmail: !usuarioEmail
      ? "Este campo es obligatorio."
      : !emailValido(normalizarEmail(usuarioEmail))
      ? "Ingresa un correo válido."
      : "",
    usuarioPassword: !usuarioPassword
      ? "Este campo es obligatorio."
      : !passwordValida(usuarioPassword)
      ? TEXTO_AYUDA_PASSWORD
      : "",
  };

  const mostrarError = (campo) => Boolean((tocados[campo] || intento) && errores[campo]);

  async function handleSubmit(e) {
    if (e) e.preventDefault();
    setError("");
    setIntento(true);

    const hayErrores = Object.keys(errores).some((campo) => Boolean(errores[campo]));
    if (hayErrores) {
      setTimeout(() => {
        document.querySelector(".field__input--invalid")?.focus();
      }, 0);
      return;
    }

    const nitTrim = nit.trim();
    const rSocialTrim = razonSocial.trim();
    const ciudadTrim = ciudad.trim();
    const correoEmpresaNorm = normalizarEmail(correoContacto);
    const nomRespTrim = usuarioNombre.trim();
    const apeRespTrim = usuarioApellido.trim();
    const correoUserNorm = normalizarEmail(usuarioEmail);

    setLoading(true);
    try {
      await request("/organizaciones/autorregistro", {
        method: "POST",
        body: {
          nit: nitTrim,
          nombre: rSocialTrim,
          codigoVerificacion,
          sector,
          numeroTrabajadores: parseInt(numeroTrabajadores, 10) || null,
          municipio: ciudadTrim,
          email: correoEmpresaNorm,
          usuarioNombre: nomRespTrim,
          usuarioApellido: apeRespTrim,
          usuarioEmail: correoUserNorm,
          usuarioPassword,
        },
      });

      navigate("/verificar-cuenta", {
        state: { email: correoUserNorm },
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
              NIT verificado: <strong>{nitInicial}</strong>. Registra los datos de tu empresa y el primer usuario Evaluador SST responsable.
            </p>

            <form className="empresas-form" onSubmit={handleSubmit} noValidate>
              <h3 style={{ fontSize: "16px", color: "var(--ink-900, #12314b)", margin: "8px 0 4px" }}>
                Datos de la Empresa
              </h3>

              <label className="field">
                <span className="field__label">Razón social</span>
                <input
                  className={`field__input ${mostrarError("razonSocial") ? "field__input--invalid" : ""}`}
                  aria-invalid={mostrarError("razonSocial") ? "true" : "false"}
                  aria-describedby={mostrarError("razonSocial") ? "razonSocial-error" : undefined}
                  placeholder="Nombre de la empresa"
                  maxLength={180}
                  value={razonSocial}
                  onChange={(e) => setRazonSocial(filtrarTextoLibre(e.target.value, 180))}
                  onBlur={() => marcar("razonSocial")}
                />
                {mostrarError("razonSocial") && (
                  <span className="field__error" id="razonSocial-error">
                    {errores.razonSocial}
                  </span>
                )}
              </label>


{/* nit */}
              <label className="field">
                <span className="field__label">NIT de la empresa </span>
                <input
                  className={`field__input ${mostrarError("nit") ? "field__input--invalid" : ""}`}
                  aria-invalid={mostrarError("nit") ? "true" : "false"}
                  aria-describedby={mostrarError("nit") ? "nit-error" : undefined}
                  placeholder="900123456-7"
                  inputMode="numeric"
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

              <label className="field">
                <span className="field__label">Código de verificación</span>
                <input
                  className={`field__input ${mostrarError("codigoVerificacion") ? "field__input--invalid" : ""}`}
                  aria-invalid={mostrarError("codigoVerificacion") ? "true" : "false"}
                  aria-describedby={mostrarError("codigoVerificacion") ? "codigoVerificacion-error" : undefined}
                  placeholder="Ej. 7"
                  inputMode="numeric"
                  maxLength={1}
                  value={codigoVerificacion}
                  onChange={(e) => setCodigoVerificacion(soloDigitos(e.target.value, 1))}
                  onBlur={() => marcar("codigoVerificacion")}
                />
                {mostrarError("codigoVerificacion") && (
                  <span className="field__error" id="codigoVerificacion-error">
                    {errores.codigoVerificacion}
                  </span>
                )}
              </label>

              <div className="empresas-form-row">
                <label className="field">
                  <span className="field__label">Sector económico</span>
                  <select
                    className={`field__input ${mostrarError("sector") ? "field__input--invalid" : ""}`}
                    aria-invalid={mostrarError("sector") ? "true" : "false"}
                    aria-describedby={mostrarError("sector") ? "sector-error" : undefined}
                    value={sector}
                    onChange={(e) => setSector(e.target.value)}
                    onBlur={() => marcar("sector")}
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
                  {mostrarError("sector") && (
                    <span className="field__error" id="sector-error">
                      {errores.sector}
                    </span>
                  )}
                </label>

                <label className="field">
                  <span className="field__label">N.º de trabajadores</span>
                  <input
                    className={`field__input ${mostrarError("numeroTrabajadores") ? "field__input--invalid" : ""}`}
                    aria-invalid={mostrarError("numeroTrabajadores") ? "true" : "false"}
                    aria-describedby={mostrarError("numeroTrabajadores") ? "numeroTrabajadores-error" : undefined}
                    type="text"
                    inputMode="numeric"
                    maxLength={7}
                    placeholder="Ej. 40"
                    value={numeroTrabajadores}
                    onChange={(e) => setNumeroTrabajadores(soloDigitos(e.target.value, 7))}
                    onBlur={() => marcar("numeroTrabajadores")}
                  />
                  {mostrarError("numeroTrabajadores") && (
                    <span className="field__error" id="numeroTrabajadores-error">
                      {errores.numeroTrabajadores}
                    </span>
                  )}
                </label>
              </div>

              <div className="empresas-form-row">
                <label className="field">
                  <span className="field__label">Ciudad / Municipio</span>
                  <input
                    className={`field__input ${mostrarError("ciudad") ? "field__input--invalid" : ""}`}
                    aria-invalid={mostrarError("ciudad") ? "true" : "false"}
                    aria-describedby={mostrarError("ciudad") ? "ciudad-error" : undefined}
                    placeholder="Ej. Neiva"
                    maxLength={80}
                    value={ciudad}
                    onChange={(e) => setCiudad(filtrarLugar(e.target.value, 80))}
                    onBlur={() => marcar("ciudad")}
                  />
                  {mostrarError("ciudad") && (
                    <span className="field__error" id="ciudad-error">
                      {errores.ciudad}
                    </span>
                  )}
                </label>

                <label className="field">
                  <span className="field__label">Correo institucional de la empresa</span>
                  <input
                    className={`field__input ${mostrarError("correoContacto") ? "field__input--invalid" : ""}`}
                    aria-invalid={mostrarError("correoContacto") ? "true" : "false"}
                    aria-describedby={mostrarError("correoContacto") ? "correoContacto-error" : undefined}
                    type="email"
                    maxLength={180}
                    placeholder="contacto@empresa.com"
                    value={correoContacto}
                    onChange={(e) => setCorreoContacto(normalizarEmail(e.target.value))}
                    onBlur={() => marcar("correoContacto")}
                  />
                  {mostrarError("correoContacto") && (
                    <span className="field__error" id="correoContacto-error">
                      {errores.correoContacto}
                    </span>
                  )}
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
                    className={`field__input ${mostrarError("usuarioNombre") ? "field__input--invalid" : ""}`}
                    aria-invalid={mostrarError("usuarioNombre") ? "true" : "false"}
                    aria-describedby={mostrarError("usuarioNombre") ? "usuarioNombre-error" : undefined}
                    placeholder="Ej. Carlos"
                    maxLength={100}
                    value={usuarioNombre}
                    onChange={(e) => setUsuarioNombre(filtrarNombrePersona(e.target.value, 100))}
                    onBlur={() => marcar("usuarioNombre")}
                  />
                  {mostrarError("usuarioNombre") && (
                    <span className="field__error" id="usuarioNombre-error">
                      {errores.usuarioNombre}
                    </span>
                  )}
                </label>

                <label className="field">
                  <span className="field__label">Apellido del responsable</span>
                  <input
                    className={`field__input ${mostrarError("usuarioApellido") ? "field__input--invalid" : ""}`}
                    aria-invalid={mostrarError("usuarioApellido") ? "true" : "false"}
                    aria-describedby={mostrarError("usuarioApellido") ? "usuarioApellido-error" : undefined}
                    placeholder="Ej. Rodríguez"
                    maxLength={100}
                    value={usuarioApellido}
                    onChange={(e) => setUsuarioApellido(filtrarNombrePersona(e.target.value, 100))}
                    onBlur={() => marcar("usuarioApellido")}
                  />
                  {mostrarError("usuarioApellido") && (
                    <span className="field__error" id="usuarioApellido-error">
                      {errores.usuarioApellido}
                    </span>
                  )}
                </label>
              </div>

              <div className="empresas-form-row">
                <label className="field">
                  <span className="field__label">Correo personal del usuario</span>
                  <input
                    className={`field__input ${mostrarError("usuarioEmail") ? "field__input--invalid" : ""}`}
                    aria-invalid={mostrarError("usuarioEmail") ? "true" : "false"}
                    aria-describedby={mostrarError("usuarioEmail") ? "usuarioEmail-error" : undefined}
                    type="email"
                    maxLength={180}
                    placeholder="carlos.rodriguez@empresa.com"
                    value={usuarioEmail}
                    onChange={(e) => setUsuarioEmail(normalizarEmail(e.target.value))}
                    onBlur={() => marcar("usuarioEmail")}
                  />
                  {mostrarError("usuarioEmail") && (
                    <span className="field__error" id="usuarioEmail-error">
                      {errores.usuarioEmail}
                    </span>
                  )}
                </label>

                <label className="field">
                  <span className="field__label">Contraseña</span>
                  <input
                    className={`field__input ${mostrarError("usuarioPassword") ? "field__input--invalid" : ""}`}
                    aria-invalid={mostrarError("usuarioPassword") ? "true" : "false"}
                    aria-describedby={mostrarError("usuarioPassword") ? "usuarioPassword-error" : undefined}
                    type="password"
                    maxLength={72}
                    placeholder="••••••••"
                    value={usuarioPassword}
                    onChange={(e) => setUsuarioPassword(e.target.value.slice(0, 72))}
                    onBlur={() => marcar("usuarioPassword")}
                  />
                  {mostrarError("usuarioPassword") && (
                    <span className="field__error" id="usuarioPassword-error">
                      {errores.usuarioPassword}
                    </span>
                  )}
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