import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { fetchPlanes } from "../api/planes";
import { etiquetaRango } from "../utils/planes";
import {
  actualizarPagoPendiente,
  guardarPagoPendiente,
  limpiarPagoPendiente,
} from "../utils/pagoPendiente";
import AppTopbar from "../components/AppTopbar";
import "../styles/app-shell.css";
import "../styles/Checkout.css";
import { request } from "../api/client";
import { enteroEnRango, soloDigitos } from "../utils/validaciones";

// ==================================================
// CONFIGURACIÓN
// ==================================================
const TARIFA_POR_BATERIA_DEFECTO = 10000; // COP
const IVA_PORCENTAJE = 0.19;
const CANTIDAD_MINIMA = 1;
const CANTIDAD_MAXIMA = 100000;
const MENSAJE_CANTIDAD_INVALIDA =
  "La cantidad debe ser un número entero entre 1 y 100.000.";
const ESTADOS_FINALES_WOMPI = ["APPROVED", "DECLINED", "VOIDED", "ERROR"];

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
// WOMPI
// ==================================================
function cargarWidgetWompi() {
  return new Promise((resolve, reject) => {
    if (window.WidgetCheckout) {
      resolve();
      return;
    }

    const scriptExistente = document.querySelector(
      'script[src="https://checkout.wompi.co/widget.js"]'
    );

    if (scriptExistente) {
      scriptExistente.addEventListener("load", () => resolve());
      scriptExistente.addEventListener("error", () => {
        reject(new Error("No se pudo cargar el Widget de Wompi."));
      });
      return;
    }

    const script = document.createElement("script");
    script.src = "https://checkout.wompi.co/widget.js";
    script.async = true;
    script.onload = () => resolve();
    script.onerror = () => {
      reject(new Error("No se pudo cargar el Widget de Wompi."));
    };
    document.body.appendChild(script);
  });
}

// ==================================================
// CHECKOUT
// ==================================================
export default function Checkout() {
  const location = useLocation();
  const navigate = useNavigate();
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

  // Con plan: precio fijo del plan (no se multiplica por la cantidad). Sin plan: cantidad x tarifa.
  const subtotal = planActual ? (cantidadValida ? planActual.precioUnitario : 0) : cantidadNumerica * tarifaActual;
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
  // PAGO WOMPI
  // ==================================================
  async function handlePagar(e) {
    if (e) {
      e.preventDefault();
    }

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
      // 1. Crear o reutilizar la compra
      const resCompra = compraId
        ? { id: compraId }
        : await request("/compras", {
          method: "POST",
          body: {
            cantidad: cantidadNumerica,
            planId: planId || null,
            bateriaNombre,
            organizacionId: usuario?.organizacionId || null,
          },
          token,
        });

      // 2. Preparar el checkout de Wompi
      const resCheckout = await request(
        `/compras/${resCompra.id}/wompi/checkout`,
        {
          method: "POST",
          token,
        }
      );

      // 3. Cargar el widget
      await cargarWidgetWompi();

      if (!window.WidgetCheckout) {
        throw new Error("El Widget de Wompi no está disponible.");
      }

      // 4. Crear el widget
      const checkout = new window.WidgetCheckout({
        currency: resCheckout.currency,
        amountInCents: resCheckout.amountInCents,
        reference: resCheckout.reference,
        publicKey: resCheckout.publicKey,
        signature: {
          integrity: resCheckout.signature,
        },
      });

      // 5. Abrir el widget
      // Se recuerda el pago en curso: si el usuario cierra sesión o la
      // sesión vence antes de que se confirme, el resultado se recupera
      // al volver a ingresar.
      guardarPagoPendiente({
        usuarioId: usuario?.id,
        compraId: resCompra.id,
        reference: resCheckout.reference,
      });

      window.scrollTo({ top: 0 });

      checkout.open(async (result) => {
        try {
          const transaction = result?.transaction;

          // El usuario cerró el widget sin crear una transacción.
          if (!transaction?.id) {
            limpiarPagoPendiente();
            return;
          }

          // Se guarda el id para poder confirmarlo luego si la llamada falla.
          actualizarPagoPendiente({ transactionId: transaction.id });

          const estadoWompi = String(transaction.status || "").toUpperCase();

          // 6. Enviar la transacción al backend
          // Se envían todos los estados devueltos por Wompi para que el
          // backend registre APPROVED, DECLINED, PENDING, ERROR y VOIDED.
          const resPago = await request("/pagos", {
            method: "POST",
            body: {
              compraId: resCompra.id,
              wompiTransactionId: transaction.id,
            },
            token,
          });

          // El backend ya registró la transacción: si el estado es final,
          // el pago deja de estar en curso.
          if (ESTADOS_FINALES_WOMPI.includes(estadoWompi)) {
            limpiarPagoPendiente();
          }

          // 7. Aprobado
          if (estadoWompi === "APPROVED" || resPago?.estado === "APROBADO") {
            navigate("/perfil", {
              state: {
                message:
                  `¡Pago aprobado! Referencia: ${resPago?.referencia || resCheckout.reference
                  }. ` + "Tu compra ha sido registrada correctamente.",
              },
            });
            return;
          }

          // 8. Rechazado
          if (estadoWompi === "DECLINED" || resPago?.estado === "RECHAZADO") {
            navigate("/perfil", {
              state: {
                message:
                  "El pago fue rechazado. El resultado quedó registrado en tu historial de compras.",
              },
            });
            return;
          }

          // 9. Cancelado
          if (estadoWompi === "VOIDED" || resPago?.estado === "VOIDED") {
            navigate("/perfil", {
              state: {
                message:
                  "El pago fue cancelado. El resultado quedó registrado en tu historial de compras.",
              },
            });
            return;
          }

          // 10. Error de pago
          if (estadoWompi === "ERROR" || resPago?.estado === "ERROR") {
            navigate("/perfil", {
              state: {
                message:
                  "Wompi reportó un error al procesar el pago. El resultado quedó registrado en tu historial de compras.",
              },
            });
            return;
          }

          // 11. Pendiente
          if (estadoWompi === "PENDING" || resPago?.estado === "PENDIENTE") {
            navigate("/perfil", {
              state: {
                message:
                  "El pago quedó pendiente de confirmación. Puedes revisar su estado desde tu historial de compras.",
              },
            });
            return;
          }

          // 12. Verificar si el webhook ya procesó la compra
          if (!resPago) {
            const compraActualizada = await request(
              `/compras/${resCompra.id}`,
              {
                method: "GET",
                token,
              }
            );

            if (compraActualizada?.estado === "PAGADA") {
              navigate("/perfil", {
                state: {
                  message:
                    "¡Pago aprobado! Tu compra ha sido registrada correctamente.",
                },
              });
              return;
            }

            setError(
              "El pago fue procesado, pero todavía no se ha podido confirmar el estado de la compra. Por favor, espera unos momentos y revisa tu historial."
            );
            return;
          }

          setError(
            resPago.mensajeRespuesta || "El pago no fue aprobado por Wompi."
          );
        } catch (err) {
          // 401: la sesión se cerró o venció, pero el pago sigue su curso en
          // Wompi. El resultado se confirma al volver a iniciar sesión.
          setError(
            err.status === 401
              ? "Tu sesión expiró, pero tu pago sigue su curso. Inicia sesión de nuevo y revisa tu historial de compras."
              : err.message || "No se pudo verificar el pago con el servidor."
          );
        } finally {
          setLoading(false);
        }
      });

      // El widget ya está abierto: el botón deja de mostrar "Procesando
      // pago..." mientras el usuario interactúa con Wompi. El resultado se
      // maneja en el callback anterior.
      setLoading(false);
    } catch (err) {
      // Compra pendiente existente
      if (err.status === 409 && err.payload?.compraId) {
        setError(
          "Ya tienes una compra pendiente de esta batería. Puedes continuar el pago desde tu historial de compras."
        );
        setLoading(false);
        return;
      }

      setError(
        err.message || "No se pudo iniciar el proceso de pago con Wompi."
      );
      setLoading(false);
    }
  }

  // ==================================================
  // RENDER
  // ==================================================
  return (
    <div className="app-shell-page">
      <AppTopbar />

      <main className="app-hero">
        <div className="app-decor app-decor--1" />
        <div className="app-decor app-decor--2" />
        <div className="app-decor app-decor--3" />

        <div className="app-content checkout-page">
          {/* VOLVER */}
          <button
            type="button"
            className="checkout-back-btn"
            onClick={() => navigate("/Inicio")}
          >
            ← Volver al inicio
          </button>

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

              {/* WOMPI */}
              <div className="checkout-wompi-box">
                <div className="checkout-wompi-icon">
                  <LockIcon />
                </div>
                <div className="checkout-wompi-content">
                  <h3>Procesado de forma segura por Wompi</h3>
                  <p>
                    Al continuar se abrirá el checkout seguro de Wompi. Allí
                    podrás seleccionar el método de pago disponible y completar
                    tu transacción.
                  </p>
                </div>
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

              {/* BOTÓN */}
              <button
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
              </button>

              {/* SEGURIDAD */}
              <div className="checkout-security-note">
                <LockIcon small />
                <span>
                  Tus datos de pago son procesados directamente por Wompi.
                </span>
              </div>

              <p className="checkout-terms">
                Al continuar aceptas los términos del servicio y la política de
                privacidad.
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
                  >
                    <option value="">Selecciona un plan</option>
                    {planes.map((p) => (
                      <option key={p.id} value={p.id}>
                        {`${etiquetaRango(p.cantidadMin, p.cantidadMax)} · ${formatCOP(p.precioUnitario)}`}
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
                  <span>{planActual ? "Precio del plan" : "Tarifa por batería"}</span>
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
                  <span>Tu información de pago es procesada por Wompi.</span>
                </div>
              </div>
            </aside>
          </div>
        </div>
      </main>
    </div>
  );
}