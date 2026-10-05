import { useState, useMemo } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import AppTopbar from "../components/AppTopbar";
import BotonRegresar from "../components/BotonRegresar";
import "../styles/app-shell.css";
import "../styles/Checkout.css";
import { request } from "../api/client";
import {
  nombrePersonaValido,
  formatearVencimiento,
  vencimientoValido,
  enteroEnRango,
  formatearTarjeta,
  soloDigitos,
  filtrarNombrePersona,
} from "../utils/validaciones";

// ==================================================
// Datos de ejemplo — ajusta según venga de tu API
// ==================================================
const TARIFA_POR_BATERIA_DEFECTO = 10000; // COP
const IVA_PORCENTAJE = 0.19;

const BANCOS_PSE = [
  { nombre: "Bancolombia", sigla: "B", color: "#FFDD00", textColor: "#111111" },
  { nombre: "Davivienda", sigla: "D", color: "#DA291C", textColor: "#ffffff" },
  { nombre: "BBVA", sigla: "BBVA", color: "#004481", textColor: "#ffffff" },
  { nombre: "Banco de Bogotá", sigla: "BB", color: "#A6192E", textColor: "#ffffff" },
  { nombre: "Banco Popular", sigla: "BP", color: "#EE3124", textColor: "#ffffff" },
  { nombre: "Nequi", sigla: "N", color: "#EE2E7B", textColor: "#ffffff" },
  { nombre: "Banco Caja Social", sigla: "CS", color: "#00558C", textColor: "#ffffff" },
  { nombre: "Banco AV Villas", sigla: "AV", color: "#F58220", textColor: "#ffffff" },
];

function formatCOP(valor) {
  return "$" + Math.round(valor).toLocaleString("es-CO");
}

function detectarMarca(numero) {
  const limpio = (numero || "").replace(/\s/g, "");
  if (/^4/.test(limpio)) return "VISA";
  if (/^5[1-5]/.test(limpio)) return "MASTERCARD";
  return null;
}

function LockIcon({ small }) {
  const size = small ? 12 : 16;
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      style={{ display: "inline-block", verticalAlign: "middle", marginRight: 6 }}
    >
      <rect x="5" y="11" width="14" height="9" rx="2" fill="currentColor" />
      <path d="M8 11V7a4 4 0 0 1 8 0v4" stroke="currentColor" strokeWidth="2" fill="none" />
    </svg>
  );
}

function VisaIcon({ size = 16 }) {
  return (
    <svg width={size * 1.7} height={size} viewBox="0 0 48 30" aria-label="Visa">
      <rect width="48" height="30" rx="4" fill="#ffffff" stroke="#E4E7F0" />
      <text
        x="24"
        y="20"
        textAnchor="middle"
        fontFamily="Arial, sans-serif"
        fontStyle="italic"
        fontWeight="700"
        fontSize="13"
        fill="#1A1F71"
      >
        VISA
      </text>
    </svg>
  );
}

function MastercardIcon({ size = 16 }) {
  return (
    <svg width={size * 1.7} height={size} viewBox="0 0 48 30" aria-label="Mastercard">
      <rect width="48" height="30" rx="4" fill="#ffffff" stroke="#E4E7F0" />
      <circle cx="20" cy="15" r="8.5" fill="#EB001B" />
      <circle cx="28" cy="15" r="8.5" fill="#F79E1B" />
      <path d="M24 8.2a8.5 8.5 0 0 1 0 13.6 8.5 8.5 0 0 1 0-13.6z" fill="#FF5F00" />
    </svg>
  );
}

function PseIcon({ size = 16 }) {
  return (
    <svg width={size * 1.7} height={size} viewBox="0 0 48 30" aria-label="PSE">
      <rect width="48" height="30" rx="4" fill="#ffffff" stroke="#E4E7F0" />
      <rect x="5" y="7" width="6" height="6" fill="#00A19A" />
      <rect x="12" y="7" width="6" height="6" fill="#8DC63F" />
      <rect x="5" y="14" width="6" height="6" fill="#0072BC" />
      <rect x="12" y="14" width="6" height="6" fill="#00A19A" />
      <text
        x="34"
        y="20"
        textAnchor="middle"
        fontFamily="Arial, sans-serif"
        fontWeight="700"
        fontSize="10"
        fill="#0072BC"
      >
        PSE
      </text>
    </svg>
  );
}

export default function Checkout() {
  const location = useLocation();
  const navigate = useNavigate();
  const { usuario, token } = useAuth();

  const {
    bateriaNombre = "Batería de Riesgo Psicosocial",
    empresaNombre = usuario?.empresa || "Tu empresa",
    tarifaPorBateria = TARIFA_POR_BATERIA_DEFECTO,
    cantidadInicial = 1,
  } = location.state || {};

  const [metodo, setMetodo] = useState("tarjeta"); // "tarjeta" | "pse"
  const [bancoSeleccionado, setBancoSeleccionado] = useState(null);
  const [cantidad, setCantidad] = useState(cantidadInicial);
  const [numeroTarjeta, setNumeroTarjeta] = useState("");
  const [nombreTarjeta, setNombreTarjeta] = useState("");
  const [vencimiento, setVencimiento] = useState("");
  const [cvv, setCvv] = useState("");
  const [guardarTarjeta, setGuardarTarjeta] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [tocados, setTocados] = useState({});
  const [intento, setIntento] = useState(false);

  const cantidadTexto = String(cantidad).trim();
  const cantidadNumerica = enteroEnRango(cantidadTexto, 1, 100000) ? Number(cantidadTexto) : 0;

  const subtotal = cantidadNumerica * tarifaPorBateria;
  const iva = subtotal * IVA_PORCENTAJE;
  const total = subtotal + iva;

  const marca = useMemo(() => detectarMarca(numeroTarjeta), [numeroTarjeta]);

  const marcarTocado = (campo) => {
    setTocados((prev) => ({ ...prev, [campo]: true }));
  };

  const errores = useMemo(() => {
    const errs = {};
    if (!enteroEnRango(cantidadTexto, 1, 100000)) {
      errs.cantidad = "La cantidad debe ser un número entero entre 1 y 100,000.";
    }

    if (metodo === "tarjeta") {
      const numLimpio = numeroTarjeta.replace(/\s/g, "");
      if (!numLimpio) {
        errs.numeroTarjeta = "Ingresa el número de tarjeta.";
      } else if (!/^\d{13,19}$/.test(numLimpio)) {
        errs.numeroTarjeta = "El número de tarjeta debe tener entre 13 y 19 dígitos.";
      }

      if (!nombreTarjeta.trim()) {
        errs.nombreTarjeta = "Ingresa el nombre en la tarjeta.";
      } else if (!nombrePersonaValido(nombreTarjeta)) {
        errs.nombreTarjeta = "Ingresa un nombre válido (solo letras, mín. 2 letras).";
      }

      if (!vencimiento.trim()) {
        errs.vencimiento = "Ingresa la fecha de vencimiento.";
      } else if (!vencimientoValido(vencimiento)) {
        errs.vencimiento = "Fecha de vencimiento inválida o tarjeta vencida.";
      }

      if (!cvv.trim()) {
        errs.cvv = "Ingresa el CVV.";
      } else if (!/^\d{3,4}$/.test(cvv)) {
        errs.cvv = "El CVV debe tener 3 o 4 dígitos.";
      }
    } else if (metodo === "pse") {
      if (!bancoSeleccionado) {
        errs.banco = "Selecciona tu banco para continuar con el pago PSE.";
      }
    }

    return errs;
  }, [cantidadTexto, metodo, numeroTarjeta, nombreTarjeta, vencimiento, cvv, bancoSeleccionado]);

  function ajustarCantidad(delta) {
    setCantidad((c) => {
      const actual = enteroEnRango(String(c).trim(), 1, 100000) ? Number(String(c).trim()) : 0;
      return Math.min(100000, Math.max(1, actual + delta));
    });
  }

  async function handlePagar(e) {
    if (e) e.preventDefault();
    setError("");
    setIntento(true);

    const numCantidad = cantidadNumerica;

    if (metodo === "tarjeta") {
      if (errores.cantidad || errores.numeroTarjeta || errores.nombreTarjeta || errores.vencimiento || errores.cvv) {
        setTimeout(() => {
          const primInvalido = document.querySelector(".field__input--invalid, .field__error");
          if (primInvalido && typeof primInvalido.focus === "function") {
            primInvalido.focus();
          }
        }, 0);
        return;
      }
    } else if (metodo === "pse") {
      if (errores.cantidad || errores.banco) {
        setTimeout(() => {
          const primInvalido = document.querySelector(".field__input--invalid, .checkout-bank-grid, .field__error");
          if (primInvalido && typeof primInvalido.focus === "function") {
            primInvalido.focus();
          }
        }, 0);
        return;
      }
    }

    setLoading(true);
    try {
      const resCompra = await request("/compras", {
        method: "POST",
        body: {
          cantidad: numCantidad,
          bateriaNombre,
          organizacionId: usuario?.organizacionId || null,
        },
        token,
      });

      const resPago = await request("/pagos", {
        method: "POST",
        body: {
          compraId: resCompra.id,
          metodo,
          numeroTarjeta: metodo === "tarjeta" ? numeroTarjeta.replace(/\s/g, "") : null,
          nombreTarjeta: metodo === "tarjeta" ? nombreTarjeta : null,
          vencimiento: metodo === "tarjeta" ? vencimiento : null,
          cvv: metodo === "tarjeta" ? cvv : null,
          banco: metodo === "pse" ? bancoSeleccionado : null,
          monto: total,
        },
        token,
      });

      if (resPago.estado === "RECHAZADO") {
        setError(resPago.mensajeRespuesta || "El pago fue rechazado por la pasarela de pagos.");
        return;
      }

      navigate("/perfil", {
        state: { message: `¡Pago exitoso! Referencia: ${resPago.referencia}. Tu compra ha sido registrada.` },
      });
    } catch (err) {
      setError(err.message || "No se pudo procesar el pago.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app-shell-page">
      <AppTopbar />

      <main className="app-hero">
        <div className="app-decor app-decor--1" />
        <div className="app-decor app-decor--2" />
        <div className="app-decor app-decor--3" />

        <div className="app-content">
          <BotonRegresar />
          <h1 className="app-title">Completa tu pago</h1>
          <p className="app-subtitle">
            {bateriaNombre} · aplicación única para {empresaNombre}
          </p>

          <div className="checkout-grid">
            {/* ===================== FORMULARIO DE PAGO ===================== */}
            <section className="app-card checkout-form-card">
              <div className="checkout-tabs">
                <button
                  type="button"
                  className={`checkout-tab ${metodo === "tarjeta" ? "checkout-tab--active" : ""}`}
                  onClick={() => setMetodo("tarjeta")}
                >
                  Tarjeta de crédito o débito
                </button>
                <button
                  type="button"
                  className={`checkout-tab ${metodo === "pse" ? "checkout-tab--active" : ""}`}
                  onClick={() => setMetodo("pse")}
                >
                  PSE
                </button>
              </div>

              {metodo === "tarjeta" ? (
                <form className="checkout-form" onSubmit={handlePagar} noValidate>
                  <label className="field">
                    <span className="field__label">Número de tarjeta</span>
                    <div className="checkout-input-with-badge">
                      <input
                        className={`field__input ${
                          errores.numeroTarjeta && (intento || tocados.numeroTarjeta) ? "field__input--invalid" : ""
                        }`}
                        inputMode="numeric"
                        maxLength={23}
                        placeholder="0000 0000 0000 0000"
                        value={numeroTarjeta}
                        onChange={(e) => setNumeroTarjeta(formatearTarjeta(e.target.value))}
                        onBlur={() => marcarTocado("numeroTarjeta")}
                        aria-invalid={!!(errores.numeroTarjeta && (intento || tocados.numeroTarjeta))}
                        aria-describedby={
                          errores.numeroTarjeta && (intento || tocados.numeroTarjeta) ? "numeroTarjeta-error" : undefined
                        }
                      />
                      {marca === "VISA" && (
                        <span className="checkout-input-icon">
                          <VisaIcon />
                        </span>
                      )}
                      {marca === "MASTERCARD" && (
                        <span className="checkout-input-icon">
                          <MastercardIcon />
                        </span>
                      )}
                    </div>
                    {errores.numeroTarjeta && (intento || tocados.numeroTarjeta) && (
                      <span className="field__error" id="numeroTarjeta-error">
                        {errores.numeroTarjeta}
                      </span>
                    )}
                  </label>

                  <label className="field">
                    <span className="field__label">Nombre en la tarjeta</span>
                    <input
                      className={`field__input ${
                        errores.nombreTarjeta && (intento || tocados.nombreTarjeta) ? "field__input--invalid" : ""
                      }`}
                      placeholder="Como aparece en la tarjeta"
                      maxLength={100}
                      value={nombreTarjeta}
                      onChange={(e) => setNombreTarjeta(filtrarNombrePersona(e.target.value, 100))}
                      onBlur={() => marcarTocado("nombreTarjeta")}
                      aria-invalid={!!(errores.nombreTarjeta && (intento || tocados.nombreTarjeta))}
                      aria-describedby={
                        errores.nombreTarjeta && (intento || tocados.nombreTarjeta) ? "nombreTarjeta-error" : undefined
                      }
                    />
                    {errores.nombreTarjeta && (intento || tocados.nombreTarjeta) && (
                      <span className="field__error" id="nombreTarjeta-error">
                        {errores.nombreTarjeta}
                      </span>
                    )}
                  </label>

                  <div className="form-row">
                    <label className="field">
                      <span className="field__label">Vencimiento (MM/AA)</span>
                      <input
                        className={`field__input ${
                          errores.vencimiento && (intento || tocados.vencimiento) ? "field__input--invalid" : ""
                        }`}
                        placeholder="MM/AA"
                        inputMode="numeric"
                        maxLength={5}
                        value={vencimiento}
                        onChange={(e) => setVencimiento(formatearVencimiento(e.target.value))}
                        onBlur={() => marcarTocado("vencimiento")}
                        aria-invalid={!!(errores.vencimiento && (intento || tocados.vencimiento))}
                        aria-describedby={
                          errores.vencimiento && (intento || tocados.vencimiento) ? "vencimiento-error" : undefined
                        }
                      />
                      {errores.vencimiento && (intento || tocados.vencimiento) && (
                        <span className="field__error" id="vencimiento-error">
                          {errores.vencimiento}
                        </span>
                      )}
                    </label>
                    <label className="field">
                      <span className="field__label">CVV</span>
                      <input
                        className={`field__input ${
                          errores.cvv && (intento || tocados.cvv) ? "field__input--invalid" : ""
                        }`}
                        placeholder="•••"
                        inputMode="numeric"
                        maxLength={4}
                        value={cvv}
                        onChange={(e) => setCvv(soloDigitos(e.target.value, 4))}
                        onBlur={() => marcarTocado("cvv")}
                        aria-invalid={!!(errores.cvv && (intento || tocados.cvv))}
                        aria-describedby={errores.cvv && (intento || tocados.cvv) ? "cvv-error" : undefined}
                      />
                      {errores.cvv && (intento || tocados.cvv) && (
                        <span className="field__error" id="cvv-error">
                          {errores.cvv}
                        </span>
                      )}
                    </label>
                  </div>

                  <label className="checkout-checkbox">
                    <input
                      type="checkbox"
                      checked={guardarTarjeta}
                      onChange={(e) => setGuardarTarjeta(e.target.checked)}
                    />
                    Guardar esta tarjeta para futuros pagos
                  </label>

                  <div className="checkout-accepted">
                    <span>Aceptamos</span>
                    <VisaIcon />
                    <MastercardIcon />
                    <PseIcon />
                  </div>

                  {error && <div className="form-message form-message--error">{error}</div>}

                  <button type="submit" className="btn-primary checkout-pay-btn" disabled={loading}>
                    <LockIcon /> {loading ? "Procesando..." : `Pagar ${formatCOP(total)}`}
                  </button>

                  <p className="checkout-terms">
                    Al confirmar aceptas los términos del servicio y la política de privacidad.
                  </p>
                </form>
              ) : (
                <div className="checkout-form">
                  <p className="auth-subtitle" style={{ margin: 0 }}>
                    Selecciona tu banco para continuar con el pago por PSE.
                  </p>

                  <div className="checkout-bank-grid">
                    {BANCOS_PSE.map((banco) => (
                      <button
                        key={banco.nombre}
                        type="button"
                        className={`checkout-bank-btn ${
                          bancoSeleccionado === banco.nombre ? "checkout-bank-btn--active" : ""
                        }`}
                        onClick={() => {
                          setBancoSeleccionado(banco.nombre);
                          marcarTocado("banco");
                        }}
                      >
                        <span
                          className="checkout-bank-icon"
                          style={{ background: banco.color, color: banco.textColor }}
                        >
                          {banco.sigla}
                        </span>
                        <span className="checkout-bank-name">{banco.nombre}</span>
                      </button>
                    ))}
                  </div>

                  {errores.banco && intento && (
                    <span className="field__error" id="banco-error">
                      {errores.banco}
                    </span>
                  )}

                  {error && <div className="form-message form-message--error">{error}</div>}

                  <button
                    type="button"
                    className="btn-primary checkout-pay-btn"
                    onClick={handlePagar}
                    disabled={loading}
                  >
                    {loading
                      ? "Redirigiendo..."
                      : `Continuar con ${bancoSeleccionado || "tu banco"} · ${formatCOP(total)}`}
                  </button>
                </div>
              )}
            </section>

            {/* ===================== RESUMEN DEL PAGO ===================== */}
            <aside className="app-card checkout-summary-card">
              <h2 className="checkout-summary-title">Resumen del pago</h2>

              <div className="checkout-summary-item">
                <strong>{bateriaNombre}</strong>
                <span className="checkout-summary-muted">Aplicación única · {empresaNombre}</span>
              </div>

              <div className="checkout-summary-row checkout-summary-row--stepper">
                <span>Cantidad de Baterías a comprar</span>
                <div className="checkout-stepper">
                  <button type="button" onClick={() => ajustarCantidad(-1)} aria-label="Restar">
                    −
                  </button>
                  <input
                    type="text"
                    inputMode="numeric"
                    maxLength={6}
                    className={`checkout-stepper-input ${
                      errores.cantidad && (intento || tocados.cantidad) ? "field__input--invalid" : ""
                    }`}
                    value={cantidad}
                    onChange={(e) => setCantidad(soloDigitos(e.target.value, 6))}
                    onBlur={() => marcarTocado("cantidad")}
                  />
                  <button type="button" onClick={() => ajustarCantidad(1)} aria-label="Sumar">
                    +
                  </button>
                </div>
              </div>
              {errores.cantidad && (intento || tocados.cantidad) && (
                <span className="field__error" id="cantidad-error">
                  {errores.cantidad}
                </span>
              )}

              <div className="checkout-summary-row">
                <span>Tarifa por Batería</span>
                <span>{formatCOP(tarifaPorBateria)}</span>
              </div>

              <div className="checkout-summary-row">
                <span>
                  Subtotal ({cantidad} x {formatCOP(tarifaPorBateria)})
                </span>
                <span>{formatCOP(subtotal)}</span>
              </div>

              <div className="checkout-summary-row">
                <span>IVA (19%)</span>
                <span>{formatCOP(iva)}</span>
              </div>

              <div className="checkout-summary-divider" />

              <div className="checkout-summary-row checkout-summary-row--total">
                <span>Total a pagar</span>
                <span>{formatCOP(total)}</span>
              </div>

              <p className="checkout-secure-note">
                <LockIcon small /> Pago seguro · tus datos viajan cifrados SSL.
              </p>
            </aside>
          </div>
        </div>
      </main>
    </div>
  );
}