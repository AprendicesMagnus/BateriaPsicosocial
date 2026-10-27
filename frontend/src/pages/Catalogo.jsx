import { useEffect, useMemo, useState } from "react";
import { useAuth } from "../context/AuthContext";
import {
  crearPedidoProductos,
  prepararCheckoutPedidoProductos,
  confirmarPagoPedidoProductos,
} from "../api/pedidosProductos";
import AppTopbar from "../components/AppTopbar";
import BotonRegresar from "../components/BotonRegresar";
import { CATEGORIAS_PRODUCTO, formatearCOP, imagenDe, useProductos } from "../data/products";
import "../styles/app-shell.css";
import "../styles/Catalogo.css";

const CLAVE_CARRITO = "magnussing_carrito_v1";

function leerCarrito() {
  try {
    const carrito = JSON.parse(localStorage.getItem(CLAVE_CARRITO) || "{}");
    return carrito && typeof carrito === "object" ? carrito : {};
  } catch {
    return {};
  }
}

function cargarWidgetWompi() {
  return new Promise((resolve, reject) => {
    if (window.WidgetCheckout) {
      resolve();
      return;
    }

    const existente = document.querySelector(
      'script[src="https://checkout.wompi.co/widget.js"]'
    );

    if (existente) {
      existente.addEventListener("load", resolve, { once: true });
      existente.addEventListener(
        "error",
        () => reject(new Error("No se pudo cargar el Widget de Wompi.")),
        { once: true }
      );
      return;
    }

    const script = document.createElement("script");
    script.src = "https://checkout.wompi.co/widget.js";
    script.async = true;
    script.onload = resolve;
    script.onerror = () =>
      reject(new Error("No se pudo cargar el Widget de Wompi."));
    document.body.appendChild(script);
  });
}

export default function Catalogo() {
  const { usuario, token } = useAuth();
  const { productos, cargando, error } = useProductos();

  const [carrito, setCarrito] = useState(leerCarrito);
  const [filtro, setFiltro] = useState("Todos");
  const [paso, setPaso] = useState("catalogo");
  const [pedido, setPedido] = useState(null);
  const [errorPago, setErrorPago] = useState("");
  const [procesandoPago, setProcesandoPago] = useState(false);

  useEffect(() => {
    try {
      localStorage.setItem(CLAVE_CARRITO, JSON.stringify(carrito));
    } catch {
      /* ignorar */
    }
  }, [carrito]);

  const lineas = useMemo(
    () =>
      Object.entries(carrito)
        .map(([id, cantidad]) => ({
          producto: productos.find((producto) => producto.id === id),
          cantidad,
        }))
        .filter((linea) => linea.producto && linea.cantidad > 0),
    [carrito, productos]
  );

  const unidades = lineas.reduce((total, linea) => total + linea.cantidad, 0);
  const subtotal = lineas.reduce(
    (total, linea) => total + linea.producto.precio * linea.cantidad,
    0
  );
  const iva = Math.round(subtotal * 0.19);
  const total = subtotal + iva;

  const cambiarCantidad = (id, delta) =>
    setCarrito((actual) => {
      const nueva = Math.max(0, Math.min(99, (actual[id] || 0) + delta));
      const { [id]: _quitado, ...resto } = actual;
      return nueva > 0 ? { ...resto, [id]: nueva } : resto;
    });

  const visibles =
    filtro === "Todos"
      ? productos
      : productos.filter((producto) => producto.categoria === filtro);

  async function iniciarPago() {
    if (!lineas.length || procesandoPago) return;

    setErrorPago("");
    setProcesandoPago(true);

    try {
      const pedidoCreado = await crearPedidoProductos(
        token,
        lineas.map(({ producto, cantidad }) => ({
          producto_id: producto.id,
          cantidad,
        }))
      );

      const checkout = await prepararCheckoutPedidoProductos(
        token,
        pedidoCreado.id
      );

      await cargarWidgetWompi();

      if (!window.WidgetCheckout) {
        throw new Error("El Widget de Wompi no está disponible.");
      }

      const widget = new window.WidgetCheckout({
        currency: checkout.currency,
        amountInCents: checkout.amountInCents,
        reference: checkout.reference,
        publicKey: checkout.publicKey,
        signature: {
          integrity: checkout.signature,
        },
      });

      widget.open(async (resultado) => {
        try {
          const transaction = resultado?.transaction;

          if (!transaction?.id) {
            setErrorPago("El pago fue cancelado antes de crear una transacción.");
            return;
          }

          const resPago = await confirmarPagoPedidoProductos(
            token,
            pedidoCreado.id,
            transaction.id
          );

          const estado = String(
            transaction.status || resPago?.estado || ""
          ).toUpperCase();

          if (estado === "APPROVED" || resPago?.pedidoEstado === "PAGADA") {
            setPedido({
              ...pedidoCreado,
              estado: "PAGADA",
            });
            setCarrito({});
            setPaso("listo");
            return;
          }

          if (estado === "PENDING") {
            setErrorPago(
              "El pago quedó pendiente de confirmación. Puedes consultar el estado del pedido desde el servidor."
            );
            return;
          }

          if (estado === "DECLINED" || resPago?.pedidoEstado === "RECHAZADO") {
            setErrorPago("El pago fue rechazado por Wompi.");
            return;
          }

          if (estado === "VOIDED") {
            setErrorPago("El pago fue cancelado.");
            return;
          }

          setErrorPago(
            resPago?.mensajeRespuesta ||
              "Wompi no aprobó el pago del pedido."
          );
        } catch (err) {
          setErrorPago(
            err.message || "No se pudo confirmar el pago con el servidor."
          );
        } finally {
          setProcesandoPago(false);
        }
      });

      setProcesandoPago(false);
    } catch (err) {
      setProcesandoPago(false);
      setErrorPago(
        err.message || "No se pudo iniciar el proceso de pago."
      );
    }
  }

  return (
    <div className="app-shell-page catalogo-fondo">
      <AppTopbar />

      <main className="app-hero">
        <div className="app-content catalogo-pagina">
          <BotonRegresar tono="oscuro" />

          <header className="catalogo-cabecera">
            <span className="catalogo-kicker">TIENDA</span>
            <h1 className="app-title">Catálogo de Productos</h1>
            <p className="app-subtitle">
              Equipos de seguridad y tecnología para tu empresa.
            </p>
          </header>

          {paso === "catalogo" && (
            <div className="catalogo-layout">
              <section className="catalogo-principal">
                <div className="catalogo-filtros">
                  {["Todos", ...CATEGORIAS_PRODUCTO].map((categoria) => (
                    <button
                      key={categoria}
                      type="button"
                      className={`catalogo-filtro ${
                        filtro === categoria ? "is-activo" : ""
                      }`}
                      aria-pressed={filtro === categoria}
                      onClick={() => setFiltro(categoria)}
                    >
                      {categoria}
                    </button>
                  ))}
                </div>

                {cargando && <p className="catalogo-vacio">Cargando productos…</p>}
                {error && <p className="catalogo-vacio">{error}</p>}

                {!cargando && !error && (
                  <div className="catalogo-grid">
                    {visibles.map((producto) => (
                      <article key={producto.id} className="producto-card">
                        <img
                          src={imagenDe(producto)}
                          alt={producto.nombre}
                          loading="lazy"
                        />
                        <div className="producto-card__cuerpo">
                          <span className="producto-card__cat">
                            {producto.categoria}
                          </span>
                          <h4>{producto.nombre}</h4>
                          <strong>{formatearCOP(producto.precio)}</strong>
                          <button
                            type="button"
                            className="catalogo-btn"
                            onClick={() => cambiarCantidad(producto.id, 1)}
                          >
                            Añadir al carrito
                          </button>
                        </div>
                      </article>
                    ))}

                    {!visibles.length && (
                      <p className="catalogo-vacio">
                        No hay productos en esta categoría.
                      </p>
                    )}
                  </div>
                )}
              </section>

              <aside className="carrito" aria-label="Carrito de compras">
                <h2>
                  Carrito{" "}
                  {unidades > 0 && (
                    <span className="carrito__contador">{unidades}</span>
                  )}
                </h2>

                {!lineas.length ? (
                  <p className="catalogo-vacio">
                    Tu carrito está vacío. Añade productos del catálogo.
                  </p>
                ) : (
                  <>
                    <ul className="carrito__lista">
                      {lineas.map(({ producto, cantidad }) => (
                        <li key={producto.id}>
                          <img src={imagenDe(producto)} alt="" />
                          <div className="carrito__info">
                            <span>{producto.nombre}</span>
                            <small>
                              {formatearCOP(producto.precio)} c/u
                            </small>
                            <div className="carrito__cantidad">
                              <button
                                type="button"
                                aria-label="Quitar uno"
                                onClick={() =>
                                  cambiarCantidad(producto.id, -1)
                                }
                              >
                                −
                              </button>
                              <span>{cantidad}</span>
                              <button
                                type="button"
                                aria-label="Añadir uno"
                                onClick={() =>
                                  cambiarCantidad(producto.id, 1)
                                }
                              >
                                +
                              </button>
                              <button
                                type="button"
                                className="carrito__quitar"
                                onClick={() =>
                                  cambiarCantidad(producto.id, -cantidad)
                                }
                              >
                                Quitar
                              </button>
                            </div>
                          </div>
                          <strong>
                            {formatearCOP(producto.precio * cantidad)}
                          </strong>
                        </li>
                      ))}
                    </ul>

                    <dl className="carrito__totales">
                      <div>
                        <dt>Subtotal</dt>
                        <dd>{formatearCOP(subtotal)}</dd>
                      </div>
                      <div>
                        <dt>IVA (19%)</dt>
                        <dd>{formatearCOP(iva)}</dd>
                      </div>
                      <div className="carrito__total">
                        <dt>Total</dt>
                        <dd>{formatearCOP(total)}</dd>
                      </div>
                    </dl>

                    <button
                      type="button"
                      className="catalogo-btn catalogo-btn--principal"
                      onClick={() => {
                        setErrorPago("");
                        setPaso("pago");
                      }}
                    >
                      Ir a pagar
                    </button>
                  </>
                )}
              </aside>
            </div>
          )}

          {paso === "pago" && (
            <section className="catalogo-pago">
              <h2>Resumen y pago</h2>

              <ul className="carrito__lista">
                {lineas.map(({ producto, cantidad }) => (
                  <li key={producto.id}>
                    <img src={imagenDe(producto)} alt="" />
                    <div className="carrito__info">
                      <span>{producto.nombre}</span>
                      <small>
                        {cantidad} × {formatearCOP(producto.precio)}
                      </small>
                    </div>
                    <strong>
                      {formatearCOP(producto.precio * cantidad)}
                    </strong>
                  </li>
                ))}
              </ul>

              <dl className="carrito__totales">
                <div>
                  <dt>Subtotal</dt>
                  <dd>{formatearCOP(subtotal)}</dd>
                </div>
                <div>
                  <dt>IVA (19%)</dt>
                  <dd>{formatearCOP(iva)}</dd>
                </div>
                <div className="carrito__total">
                  <dt>Total a pagar</dt>
                  <dd>{formatearCOP(total)}</dd>
                </div>
              </dl>

              {errorPago && (
                <p className="catalogo-nota">{errorPago}</p>
              )}

              <p className="catalogo-nota">
                El valor final se calcula nuevamente en el backend con los
                precios guardados en la base de datos.
              </p>

              <div className="catalogo-pago__acciones">
                <button
                  type="button"
                  className="catalogo-btn"
                  onClick={() => setPaso("catalogo")}
                  disabled={procesandoPago}
                >
                  ← Seguir comprando
                </button>

                <button
                  type="button"
                  className="catalogo-btn catalogo-btn--principal"
                  onClick={iniciarPago}
                  disabled={!lineas.length || procesandoPago}
                >
                  {procesandoPago
                    ? "Preparando pago..."
                    : `Pagar · ${formatearCOP(total)}`}
                </button>
              </div>
            </section>
          )}

          {paso === "listo" && pedido && (
            <section className="catalogo-pago catalogo-pago--listo">
              <div className="catalogo-check" aria-hidden="true">
                ✓
              </div>
              <h2>¡Pedido pagado!</h2>
              <p>
                Número de pedido: <strong>{pedido.numero}</strong>
              </p>
              <p>
                {pedido.items?.length || 0} producto(s) · Total{" "}
                {formatearCOP(pedido.total)}
              </p>
              <p>{usuario?.email || usuario?.correo || ""}</p>

              <button
                type="button"
                className="catalogo-btn catalogo-btn--principal"
                onClick={() => {
                  setPedido(null);
                  setErrorPago("");
                  setPaso("catalogo");
                }}
              >
                Volver al catálogo
              </button>
            </section>
          )}
        </div>
      </main>
    </div>
  );
}
