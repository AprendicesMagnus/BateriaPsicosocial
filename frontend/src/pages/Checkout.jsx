import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
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
      <rect
        x="5"
        y="11"
        width="14"
        height="9"
        rx="2"
        fill="currentColor"
      />
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
        reject(
          new Error("No se pudo cargar el Widget de Wompi.")
        );
      });
      return;
    }
    const script = document.createElement("script");
    script.src = "https://checkout.wompi.co/widget.js";
    script.async = true;
    script.onload = () => resolve();
    script.onerror = () => {
      reject(
        new Error("No se pudo cargar el Widget de Wompi.")
      );
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
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [intento, setIntento] = useState(false);
  const [cantidadTocada, setCantidadTocada] = useState(false);
  // ==================================================
  // CÁLCULOS
  // ==================================================
  const cantidadTexto = String(cantidad).trim();
  const cantidadNumerica = enteroEnRango(
    cantidadTexto,
    1,
    100000
  )
    ? Number(cantidadTexto)
    : 0;
  const cantidadValida = enteroEnRango(
    cantidadTexto,
    1,
    100000
  );
  const subtotal =
    cantidadNumerica * tarifaPorBateria;
  const iva =
    subtotal * IVA_PORCENTAJE;
  const total =
    subtotal + iva;
  const esCompraExistente = Boolean(compraId);
  const totalMostrado =
    esCompraExistente && Number(totalCompra) > 0
      ? Number(totalCompra)
      : total;
  const subtotalMostrado =
    totalMostrado / (1 + IVA_PORCENTAJE);
  const ivaMostrado =
    totalMostrado - subtotalMostrado;
  // ==================================================
  // CANTIDAD
  // ==================================================
  function ajustarCantidad(delta) {
    setCantidad((actual) => {
      const valorActual = enteroEnRango(
        String(actual).trim(),
        1,
        100000
      )
        ? Number(String(actual).trim())
        : 0;
      return Math.min(
        100000,
        Math.max(1, valorActual + delta)
      );
    });
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
    if (!cantidadValida) {
      setError(
        "La cantidad debe ser un número entero entre 1 y 100.000."
      );
      return;
    }
    setLoading(true);
    try {
      // ==================================================
      // 1. CREAR O REUTILIZAR COMPRA
      // ==================================================
      const resCompra = compraId
        ? { id: compraId }
        : await request("/compras", {
          method: "POST",
          body: {
            cantidad: cantidadNumerica,
            bateriaNombre,
            organizacionId:
              usuario?.organizacionId || null,
          },
          token,
        });
      // ==================================================
      // 2. PREPARAR CHECKOUT WOMPI
      // ==================================================
      const resCheckout = await request(
        `/compras/${resCompra.id}/wompi/checkout`,
        {
          method: "POST",
          token,
        }
      );
      // ==================================================
      // 3. CARGAR WIDGET
      // ==================================================
      await cargarWidgetWompi();
      if (!window.WidgetCheckout) {
        throw new Error(
          "El Widget de Wompi no está disponible."
        );
      }
      // ==================================================
      // 4. CREAR WIDGET
      // ==================================================
      const checkout =
        new window.WidgetCheckout({
          currency: resCheckout.currency,
          amountInCents:
            resCheckout.amountInCents,
          reference: resCheckout.reference,
          publicKey: resCheckout.publicKey,
          signature: {
            integrity:
              resCheckout.signature,
          },
        });
      // ==================================================
      // 5. ABRIR WIDGET
      // ==================================================
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
          const transaction =
            result?.transaction;
          if (!transaction?.id) {
            // El usuario cerró el widget sin crear una transacción.
            limpiarPagoPendiente();
            setError(
              "Wompi no devolvió un identificador de transacción."
            );
            setLoading(false);
            return;
          }
          // ==================================================
          // VALIDAR ESTADO DE LA TRANSACCIÓN
          // ==================================================
          // Se guarda el id para poder confirmarlo luego si esta llamada falla.
          actualizarPagoPendiente({ transactionId: transaction.id });
          const estadoWompi = String(
            transaction.status || ""
          ).toUpperCase();
          // ==================================================
          // 6. ENVIAR TRANSACCIÓN AL BACKEND
          // ==================================================
          //
          // IMPORTANTE:
          // Todos los estados devueltos por Wompi se envían
          // al backend. Esto permite que el backend registre
          // correctamente APPROVED, DECLINED, PENDING,
          // ERROR y VOIDED.
          //
          const resPago = await request(
            "/pagos",
            {
              method: "POST",
              body: {
                compraId: resCompra.id,
                wompiTransactionId:
                  transaction.id,
              },
              token,
            }
          );
          // El backend ya registró la transacción: si el estado es final,
          // el pago deja de estar "en curso".
          if (["APPROVED", "DECLINED", "VOIDED", "ERROR"].includes(estadoWompi)) {
            limpiarPagoPendiente();
          }
          // ==================================================
          // 7. RESULTADO FINAL - APROBADO
          // ==================================================
          if (
            estadoWompi === "APPROVED" ||
            resPago?.estado === "APROBADO"
          ) {
            navigate("/perfil", {
              state: {
                message:
                  `¡Pago aprobado! Referencia: ${resPago?.referencia ||
                  resCheckout.reference
                  }. ` +
                  "Tu compra ha sido registrada correctamente.",
              },
            });
            return;
          }
          // ==================================================
          // 8. PAGO RECHAZADO
          // ==================================================
          if (
            estadoWompi === "DECLINED" ||
            resPago?.estado === "RECHAZADO"
          ) {
            navigate("/perfil", {
              state: {
                message:
                  "El pago fue rechazado. El resultado quedó registrado en tu historial de compras.",
              },
            });
            return;
          }
          // ==================================================
          // 9. PAGO CANCELADO
          // ==================================================
          if (
            estadoWompi === "VOIDED" ||
            resPago?.estado === "VOIDED"
          ) {
            navigate("/perfil", {
              state: {
                message:
                  "El pago fue cancelado. El resultado quedó registrado en tu historial de compras.",
              },
            });
            return;
          }
          // ==================================================
          // 10. ERROR DE PAGO
          // ==================================================
          if (
            estadoWompi === "ERROR" ||
            resPago?.estado === "ERROR"
          ) {
            navigate("/perfil", {
              state: {
                message:
                  "Wompi reportó un error al procesar el pago. El resultado quedó registrado en tu historial de compras.",
              },
            });
            return;
          }
          // ==================================================
          // 11. PAGO PENDIENTE
          // ==================================================
          if (
            estadoWompi === "PENDING" ||
            resPago?.estado === "PENDIENTE"
          ) {
            navigate("/perfil", {
              state: {
                message:
                  "El pago quedó pendiente de confirmación. Puedes revisar su estado desde tu historial de compras.",
              },
            });
            return;
          }
          // ==================================================
          // 12. VERIFICAR SI EL WEBHOOK YA PROCESÓ LA COMPRA
          // ==================================================
          if (!resPago) {
            const compraActualizada =
              await request(
                `/compras/${resCompra.id}`,
                {
                  method: "GET",
                  token,
                }
              );
            if (
              compraActualizada?.estado ===
              "PAGADA"
            ) {
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
            resPago.mensajeRespuesta ||
            "El pago no fue aprobado por Wompi."
          );
        } catch (err) {
          // 401: la sesión se cerró o venció, pero el pago sigue su curso en Wompi.
          // El resultado se confirma al volver a iniciar sesión.
          setError(
            err.status === 401
              ? "Tu sesión expiró, pero tu pago sigue su curso. Inicia sesión de nuevo y revisa tu historial de compras."
              : err.message ||
              "No se pudo verificar el pago con el servidor."
          );
        } finally {
          setLoading(false);
        }
      });
      // ==================================================
      // WOMPI YA ESTÁ ABIERTO
      // ==================================================
      //
      // Ya no necesitamos mantener el botón de MagnusSIG
      // en "Procesando pago..." mientras el usuario
      // interactúa con el Widget.
      //
      // El resultado de la transacción será manejado
      // por el callback anterior.
      //
      setLoading(false);
    } catch (err) {
      // ==================================================
      // COMPRA PENDIENTE EXISTENTE
      // ==================================================
      if (
        err.status === 409 &&
        err.payload?.compraId
      ) {
        setError(
          "Ya tienes una compra pendiente de esta batería. Puedes continuar el pago desde tu historial de compras."
        );
        setLoading(false);
        return;
      }
      setError(
        err.message ||
        "No se pudo iniciar el proceso de pago con Wompi."
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
            onClick={() =>
              navigate("/Inicio")
            }
          >
            ← Volver al inicio
          </button>
          {/* BREADCRUMB */}
          <nav className="app-breadcrumb">
            Evaluaciones
            <span>›</span>
            Pago de la batería
          </nav>
          {/* ENCABEZADO */}
          <div className="checkout-heading">
            <div>
              <span className="checkout-heading-kicker">
                COMPRA SEGURA
              </span>
              <h1 className="app-title">
                Completa tu pago
              </h1>
              <p className="app-subtitle">
                {bateriaNombre} · aplicación única
                para {empresaNombre}
              </p>
            </div>
          </div>
          {/* CONTENIDO */}
          {esCompraExistente && (
            <div
              style={{
                marginBottom: "18px",
                padding: "14px 16px",
                borderRadius: "12px",
                background: "#eff6ff",
                border: "1px solid #bfdbfe",
                color: "#1e3a8a",
                fontSize: "14px",
                lineHeight: 1.5,
              }}
            >
              <strong>Compra pendiente</strong>
              <br />
              Estás continuando una compra que ya habías iniciado.
              No se creará una nueva compra.
            </div>
          )}
          <div className="checkout-grid checkout-grid--modern">
            {/* ==================================================
                PAGO
            ================================================== */}
            <section className="app-card checkout-form-card checkout-payment-card">
              <div className="checkout-section-header">
                <div className="checkout-section-number">
                  01
                </div>
                <div>
                  <span className="checkout-section-kicker">
                    MÉTODO DE PAGO
                  </span>
                  <h2 className="checkout-section-title">
                    Pago seguro
                  </h2>
                </div>
              </div>
              {/* WOMPI */}
              <div className="checkout-wompi-box">
                <div className="checkout-wompi-icon">
                  <LockIcon />
                </div>
                <div className="checkout-wompi-content">
                  <h3>
                    Procesado de forma segura
                    por Wompi
                  </h3>
                  <p>
                    Al continuar se abrirá el
                    checkout seguro de Wompi.
                    Allí podrás seleccionar el
                    método de pago disponible
                    y completar tu transacción.
                  </p>
                </div>
              </div>
              {/* TOTAL */}
              <div className="checkout-payment-amount">
                <span>
                  Total a pagar
                </span>
                <strong>
                  {formatCOP(totalMostrado)}
                </strong>
              </div>
              {/* ERROR */}
              {error && (
                <div className="form-message form-message--error">
                  {error}
                </div>
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
                {!loading && (
                  <span className="checkout-pay-arrow">
                    →
                  </span>
                )}
              </button>
              {/* SEGURIDAD */}
              <div className="checkout-security-note">
                <LockIcon small />
                <span>
                  Tus datos de pago son
                  procesados directamente
                  por Wompi.
                </span>
              </div>
              <p className="checkout-terms">
                Al continuar aceptas los términos
                del servicio y la política de
                privacidad.
              </p>
            </section>
            {/* ==================================================
                RESUMEN
            ================================================== */}
            <aside className="app-card checkout-summary-card checkout-summary-card--modern">
              <div className="checkout-section-header">
                <div className="checkout-section-number">
                  02
                </div>
                <div>
                  <span className="checkout-section-kicker">
                    RESUMEN
                  </span>
                  <h2 className="checkout-section-title">
                    Tu compra
                  </h2>
                </div>
              </div>
              {/* PRODUCTO */}
              <div className="checkout-product">
                <div className="checkout-product-icon">
                  ✓
                </div>
                <div className="checkout-product-info">
                  <strong>
                    {bateriaNombre}
                  </strong>
                  <span>
                    Aplicación única
                  </span>
                </div>
              </div>
              {/* CANTIDAD */}
              <div className="checkout-quantity-section">
                <div>
                  <span className="checkout-detail-label">
                    Cantidad
                  </span>
                  <span className="checkout-detail-description">
                    Baterías a comprar
                  </span>
                </div>
                <div className="checkout-stepper">
                  <button
                    type="button"
                    onClick={() =>
                      ajustarCantidad(-1)
                    }
                    aria-label="Restar"
                    disabled={
                      esCompraExistente ||
                      cantidad <= 1
                    }
                  >
                    −
                  </button>
                  <input
                    type="text"
                    inputMode="numeric"
                    maxLength={6}
                    className={`checkout-stepper-input ${!cantidadValida &&
                      (intento ||
                        cantidadTocada)
                      ? "field__input--invalid"
                      : ""
                      }`}
                    value={cantidad}
                    disabled={esCompraExistente}
                    onChange={(e) =>
                      setCantidad(
                        soloDigitos(
                          e.target.value,
                          6
                        )
                      )
                    }
                    onBlur={() =>
                      setCantidadTocada(
                        true
                      )
                    }
                    aria-label="Cantidad de baterías"
                  />
                  <button
                    type="button"
                    onClick={() =>
                      ajustarCantidad(1)
                    }
                    aria-label="Sumar"
                    disabled={
                      esCompraExistente ||
                      cantidad >= 100000
                    }
                  >
                    +
                  </button>
                </div>
              </div>
              {/* ERROR CANTIDAD */}
              {!cantidadValida &&
                (intento ||
                  cantidadTocada) && (
                  <span
                    className="field__error"
                    id="cantidad-error"
                  >
                    La cantidad debe ser un
                    número entero entre 1 y
                    100.000.
                  </span>
                )}
              {/* PRECIOS */}
              <div className="checkout-price-list">
                <div className="checkout-price-row">
                  <span>
                    Tarifa por batería
                  </span>
                  <strong>
                    {formatCOP(
                      tarifaPorBateria
                    )}
                  </strong>
                </div>
                <div className="checkout-price-row">
                  <span>
                    Subtotal
                  </span>
                  <strong>
                    {formatCOP(
                      subtotal
                    )}
                  </strong>
                </div>
                <div className="checkout-price-row">
                  <span>
                    IVA <small>(19%)</small>
                  </span>
                  <strong>
                    {formatCOP(ivaMostrado)}
                  </strong>
                </div>
              </div>
              {/* TOTAL */}
              <div className="checkout-total">
                <div>
                  <span>
                    Total a pagar
                  </span>
                  <small>
                    Impuestos incluidos
                  </small>
                </div>
                <strong>
                  {formatCOP(totalMostrado)}
                </strong>
              </div>
              {/* SEGURIDAD */}
              <div className="checkout-summary-security">
                <div className="checkout-security-icon">
                  <LockIcon small />
                </div>
                <div>
                  <strong>
                    Pago seguro
                  </strong>
                  <span>
                    Tu información de pago
                    es procesada por Wompi.
                  </span>
                </div>
              </div>
            </aside>
          </div>
        </div>
      </main>
    </div>
  );
}