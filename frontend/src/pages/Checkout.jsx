import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { fetchPlanes } from "../api/planes";
import { etiquetaRango } from "../utils/planes";
import AppTopbar from "../components/AppTopbar";
import BotonRegresar from "../components/BotonRegresar";
import "../styles/app-shell.css";
import "../styles/Checkout.css";
import { request } from "../api/client";
import { enteroEnRango, soloDigitos } from "../utils/validaciones";
import PagoNequi from "../components/PagoNequi";

// ==================================================
// CONFIGURACIÓN
// ==================================================
const TARIFA_POR_BATERIA_DEFECTO = 10000; // COP
const IVA_PORCENTAJE = 0.19;
const CANTIDAD_MINIMA = 1;
const CANTIDAD_MAXIMA = 100000;
const MENSAJE_CANTIDAD_INVALIDA =
  "La cantidad debe ser un número entero entre 1 y 100.000.";

// ==================================================
// UTILIDADES
// ==================================================
function formatCOP(valor) {
  return "$" + Math.round(valor).toLocaleString("es-CO");
}

function LockIcon({ small = false }) {
  const size = small ? 12 : 16;

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
      className="checkout-lock-icon"
    >
      <rect x="5" y="11" width="14" height="9" rx="2" fill="currentColor" />
      <path
        d="M8 11V7a4 4 0 0 1 8 0v4"
        stroke="currentColor"
        strokeWidth="2"
        fill="none"
      />
    </svg>
  );
}

// ==================================================
// MÉTODO DE PAGO
// ==================================================
// ==================================================
// CHECKOUT
// ==================================================
export default function Checkout() {
  const location = useLocation();
  const { usuario, token } = useAuth();

  const {
    bateriaNombre = "Batería de Riesgo Psicosocial",
    empresaNombre = usuario?.empresa || "Tu empresa",
    tarifaPorBateria = TARIFA_POR_BATERIA_DEFECTO,
    cantidadInicial = 1,
    compraId = null,
    totalCompra = null,
  } = location.state || {};

  // ==================================================
  // ESTADOS
  // ==================================================
  const [cantidad, setCantidad] = useState(cantidadInicial);

  // Plan elegido (rango de baterías + precio por batería). Los administra el Super Administrador.
  const [planes, setPlanes] = useState([]);
  const [planId, setPlanId] = useState("");
  useEffect(() => {
    fetchPlanes()
      .then((lista) => setPlanes(lista || []))
      .catch(() => {});
  }, []);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [intento, setIntento] = useState(false);
  const [cantidadTocada, setCantidadTocada] = useState(false);
  const [compraNequiId, setCompraNequiId] = useState(compraId);

  // ==================================================
  // CÁLCULOS
  // ==================================================
  const planActual = planes.find((p) => p.id === planId) || null;
  const tarifaActual = planActual ? planActual.precioUnitario : tarifaPorBateria;
  const cantidadMinima = planActual ? planActual.cantidadMin : CANTIDAD_MINIMA;
  const cantidadMaxima = planActual?.cantidadMax ?? CANTIDAD_MAXIMA;
  const mensajeCantidad = planActual
    ? `Para este plan la cantidad debe estar entre ${cantidadMinima} y ${planActual.cantidadMax ?? "100.000"}.`
    : MENSAJE_CANTIDAD_INVALIDA;

  const cantidadTexto = String(cantidad).trim();
  const cantidadValida = enteroEnRango(
    cantidadTexto,
    cantidadMinima,
    cantidadMaxima
  );
  const cantidadNumerica = cantidadValida ? Number(cantidadTexto) : 0;

  const subtotal = cantidadNumerica * tarifaActual;
  const iva = subtotal * IVA_PORCENTAJE;
  const total = subtotal + iva;

  const esCompraExistente = Boolean(compraId);
  const totalMostrado =
    esCompraExistente && Number(totalCompra) > 0 ? Number(totalCompra) : total;
  const subtotalMostrado = totalMostrado / (1 + IVA_PORCENTAJE);
  const ivaMostrado = totalMostrado - subtotalMostrado;

  const mostrarErrorCantidad = !cantidadValida && (intento || cantidadTocada);

  // ==================================================
  // CANTIDAD
  // ==================================================
  function ajustarCantidad(delta) {
    setCantidad((actual) => {
      const texto = String(actual).trim();
      const valorActual = enteroEnRango(texto, cantidadMinima, cantidadMaxima)
        ? Number(texto)
        : 0;

      return Math.min(
        cantidadMaxima,
        Math.max(cantidadMinima, valorActual + delta)
      );
    });
  }

  function elegirPlan(id) {
    setPlanId(id);
    setError("");
    const plan = planes.find((p) => p.id === id);
    if (plan) {
      // Si la cantidad actual no cabe en el plan, se ajusta al mínimo del plan.
      setCantidad((actual) => {
        const n = Number(actual);
        const cabe = n >= plan.cantidadMin && (plan.cantidadMax == null || n <= plan.cantidadMax);
        return cabe ? n : plan.cantidadMin;
      });
    }
  }

  // ==================================================
  // PAGO MANUAL NEQUI
  // ==================================================
  async function handlePagar(e) {
    e?.preventDefault();
    setError("");
    setIntento(true);
    if (!compraId && planes.length > 0 && !planId) {
      setError("Selecciona un plan para continuar.");
      return;
    }
    if (!cantidadValida) {
      setError(mensajeCantidad);
      return;
    }
    setLoading(true);
    try {
      const resCompra = compraId
        ? { id: compraId }
        : await request("/compras", {
            method: "POST",
            body: { cantidad: cantidadNumerica, planId: planId || null, bateriaNombre, organizacionId: usuario?.organizacionId || null },
            token,
          });
      setCompraNequiId(resCompra.id);
    } catch (err) {
      if (err.status === 409 && err.payload?.compraId) {
        setError("Ya tienes una compra pendiente. Continúa el pago desde tu historial de compras.");
      } else {
        setError(err.message || "No se pudo registrar la compra.");
      }
    } finally {
      setLoading(false);
    }
  }

  // ==================================================
  // RENDER
  // ==================================================
  return (
    <div className="app-shell-page">
      <AppTopbar />

      <main id="contenido-principal" tabIndex={-1} className="app-hero">
        <div className="app-decor app-decor--1" />
        <div className="app-decor app-decor--2" />
        <div className="app-decor app-decor--3" />

        <div className="app-content checkout-page">
          {/* VOLVER */}
          <BotonRegresar to="/Inicio" />

          {/* ENCABEZADO */}
          <div className="checkout-heading">
            <div>
              <span className="checkout-heading-kicker">COMPRA SEGURA</span>
              <h1 className="app-title">Completa tu pago</h1>
              <p className="app-subtitle">
                {bateriaNombre} · aplicación única para {empresaNombre}
              </p>
            </div>
          </div>

          {/* AVISO DE COMPRA PENDIENTE */}
          {esCompraExistente && (
            <div className="checkout-pending-notice">
              <strong>Compra pendiente</strong>
              <br />
              Estás continuando una compra que ya habías iniciado. No se creará
              una nueva compra.
            </div>
          )}

          <div className="checkout-grid checkout-grid--modern">
            {/* PAGO */}
            <section className="app-card checkout-form-card checkout-payment-card">
              <div className="checkout-section-header">
                <div className="checkout-section-number">01</div>
                <div>
                  <span className="checkout-section-kicker">MÉTODO DE PAGO</span>
                  <h2 className="checkout-section-title">Pago seguro</h2>
                </div>
              </div>

              <div className="checkout-wompi-box">
                <div className="checkout-wompi-icon"><LockIcon /></div>
                <div className="checkout-wompi-content">
                  <h3>Pago manual mediante Nequi QR</h3>
                  <p>Escanea el código QR de Nequi Negocios, transfiere el valor exacto y adjunta el comprobante. La compra solo se activa cuando un administrador apruebe el pago.</p>
                </div>
              </div>

              {/* QUÉ SIGUE */}
              <div className="checkout-siguiente">
                <h3>¿Qué pasa después de pagar?</h3>
                <ol>
                  <li>
                    <span>1</span>
                    <div>
                      <strong>Transfieres mediante Nequi QR</strong>
                      <small>Escaneas el código y pagas el valor exacto.</small>
                    </div>
                  </li>
                  <li>
                    <span>2</span>
                    <div>
                      <strong>Revisamos tu comprobante</strong>
                      <small>Un administrador verifica y aprueba la transferencia.</small>
                    </div>
                  </li>
                  <li>
                    <span>3</span>
                    <div>
                      <strong>Tus baterías quedan disponibles</strong>
                      <small>Las verás en tu empresa y el recibo en Perfil → Historial de compras.</small>
                    </div>
                  </li>
                </ol>
              </div>

              {/* TOTAL */}
              <div className="checkout-payment-amount">
                <span>Total a pagar</span>
                <strong>{formatCOP(totalMostrado)}</strong>
              </div>

              {/* ERROR */}
              {error && (
                <div className="form-message form-message--error">{error}</div>
              )}

              {!compraNequiId && <button
                type="button"
                className="btn-primary checkout-pay-btn checkout-pay-btn--large"
                onClick={handlePagar}
                disabled={loading}
              >
                <LockIcon />
                <span>
                  {loading
                    ? "Procesando pago..."
                    : `Continuar con el pago · ${formatCOP(totalMostrado)}`}
                </span>
                {!loading && <span className="checkout-pay-arrow">→</span>}
              </button>}

              {compraNequiId && <PagoNequi tipo="bateria" compraId={compraNequiId} token={token} total={totalMostrado} onComplete={() => setError("Comprobante enviado. Consulta el estado de la compra en Perfil → Historial de compras.")} />}

              {!compraNequiId && <div className="checkout-security-note"><LockIcon small /><span>El comprobante será revisado antes de habilitar tus baterías.</span></div>}

              <p className="checkout-terms">
                Al continuar aceptas los términos del servicio y la{" "}
                <Link to="/politica-de-datos" target="_blank" rel="noopener noreferrer" className="politica-enlace-checkout">política de privacidad</Link>.
              </p>
            </section>

            {/* RESUMEN */}
            <aside className="app-card checkout-summary-card checkout-summary-card--modern">
              <div className="checkout-section-header">
                <div className="checkout-section-number">02</div>
                <div>
                  <span className="checkout-section-kicker">RESUMEN</span>
                  <h2 className="checkout-section-title">Tu compra</h2>
                </div>
              </div>

              {/* PRODUCTO */}
              <div className="checkout-product">
                <div className="checkout-product-icon">✓</div>
                <div className="checkout-product-info">
                  <strong>{bateriaNombre}</strong>
                  <span>Aplicación única</span>
                </div>
              </div>

              {/* PLAN */}
              {!esCompraExistente && planes.length > 0 && (
                <div className="checkout-plan-section" style={{ display: "flex", flexDirection: "column", gap: 6, margin: "14px 0" }}>
                  <label className="checkout-detail-label" htmlFor="checkout-plan">
                    Plan
                  </label>
                  <select
                    id="checkout-plan"
                    className="field__input"
                    value={planId}
                    onChange={(e) => elegirPlan(e.target.value)}
                    disabled={loading}
                    aria-required="true"
                  >
                    <option value="">Selecciona un plan</option>
                    {planes.map((p) => (
                      <option key={p.id} value={p.id}>
                        {`${etiquetaRango(p.cantidadMin, p.cantidadMax)} · ${formatCOP(p.precioUnitario)} c/u`}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {/* CANTIDAD */}
              <div className="checkout-quantity-section">
                <div>
                  <span className="checkout-detail-label">Cantidad</span>
                  <span className="checkout-detail-description">
                    Baterías a comprar
                  </span>
                </div>

                <div className="checkout-stepper">
                  <button
                    type="button"
                    onClick={() => ajustarCantidad(-1)}
                    aria-label="Restar"
                    disabled={esCompraExistente || cantidadNumerica <= cantidadMinima}
                  >
                    −
                  </button>

                  <input
                    type="text"
                    inputMode="numeric"
                    maxLength={6}
                    className={`checkout-stepper-input ${mostrarErrorCantidad ? "field__input--invalid" : ""
                      }`}
                    value={cantidad}
                    disabled={esCompraExistente}
                    onChange={(e) => setCantidad(soloDigitos(e.target.value, 6))}
                    onBlur={() => setCantidadTocada(true)}
                    aria-label="Cantidad de baterías"
                    aria-required="true"
                    aria-invalid={mostrarErrorCantidad}
                    aria-describedby={
                      mostrarErrorCantidad ? "cantidad-error" : undefined
                    }
                  />

                  <button
                    type="button"
                    onClick={() => ajustarCantidad(1)}
                    aria-label="Sumar"
                    disabled={esCompraExistente || cantidadNumerica >= cantidadMaxima}
                  >
                    +
                  </button>
                </div>
              </div>

              {/* ERROR CANTIDAD */}
              {mostrarErrorCantidad && (
                <span className="field__error" id="cantidad-error">
                  {mensajeCantidad}
                </span>
              )}

              {/* PRECIOS */}
              <div className="checkout-price-list">
                <div className="checkout-price-row">
                  <span>Tarifa por batería</span>
                  <strong>{formatCOP(tarifaActual)}</strong>
                </div>
                <div className="checkout-price-row">
                  <span>Subtotal</span>
                  <strong>{formatCOP(subtotalMostrado)}</strong>
                </div>
                <div className="checkout-price-row">
                  <span>
                    IVA <small>(19%)</small>
                  </span>
                  <strong>{formatCOP(ivaMostrado)}</strong>
                </div>
              </div>

              {/* TOTAL */}
              <div className="checkout-total">
                <div>
                  <span>Total a pagar</span>
                  <small>Impuestos incluidos</small>
                </div>
                <strong>{formatCOP(totalMostrado)}</strong>
              </div>

              {/* SEGURIDAD */}
              <div className="checkout-summary-security">
                <div className="checkout-security-icon">
                  <LockIcon small />
                </div>
                <div>
                  <strong>Pago seguro</strong>
                  <span>Tu comprobante será verificado por un administrador antes de activar las baterías.</span>
                </div>
              </div>
            </aside>
          </div>
        </div>
      </main>
    </div>
  );
}