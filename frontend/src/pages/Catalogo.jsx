import { useEffect, useMemo, useState } from "react";
import { useAuth } from "../context/AuthContext";
import {
  crearPedidoProductos,
  prepararCheckoutPedidoProductos,
  confirmarPagoPedidoProductos,
  obtenerPedidoProductos,
} from "../api/pedidosProductos";
import AppTopbar from "../components/AppTopbar";
import BotonRegresar from "../components/BotonRegresar";
import { categoriasDe, formatearCOP, imagenDe, manejaStock, useProductos } from "../data/products";
import "../styles/app-shell.css";
import "../styles/Catalogo.css";

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

  // El carrito comienza vacío al iniciar el catálogo. Se conserva mientras
  // el usuario navega por esta pantalla, pero no recupera selecciones antiguas.
  const [carrito, setCarrito] = useState({});
  const [filtro, setFiltro] = useState("Todos");
  const [paso, setPaso] = useState("catalogo");
  const [pedido, setPedido] = useState(null);
  const [errorPago, setErrorPago] = useState("");
  const [procesandoPago, setProcesandoPago] = useState(false);

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
      const producto = productos.find((p) => p.id === id);
      const maximo = producto && !manejaStock(producto) ? 99 : Math.min(99, Number(producto?.stock ?? 0));
      const nueva = Math.max(0, Math.min(maximo, (actual[id] || 0) + delta));
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
            setErrorPago("El pago no se completó. Puedes revisar o cancelar el pedido desde tu perfil.");
            return;
          }

          const resPago = await confirmarPagoPedidoProductos(
            token,
            pedidoCreado.id,
            transaction.id
          );
          const pedidoActualizado = await obtenerPedidoProductos(token, pedidoCreado.id);
          const estadoWompi = String(
            transaction.status || resPago?.wompiStatus || resPago?.estado || ""
          ).toUpperCase();
          const estadoPedido = String(
            pedidoActualizado?.estado || resPago?.pedidoEstado || ""
          ).toUpperCase();

          if (estadoWompi === "APPROVED" || estadoPedido === "PAGADA") {
            setPedido(pedidoActualizado);
            setCarrito({});
            setPaso("listo");
            return;
          }

          if (estadoWompi === "PENDING" || estadoPedido === "PENDIENTE") {
            setErrorPago("El pago quedó pendiente de confirmación. Puedes consultar el pedido desde tu perfil.");
            return;
          }

          if (estadoWompi === "DECLINED" || estadoPedido === "RECHAZADO") {
            setErrorPago("El pago fue rechazado por Wompi. Puedes reintentarlo desde el historial de pedidos de tu perfil.");
            return;
          }

          if (estadoWompi === "VOIDED" || estadoPedido === "CANCELADA") {
            setErrorPago("El pago fue cancelado. Puedes realizar un nuevo pedido cuando lo desees.");
            return;
          }

          if (estadoWompi === "ERROR" || estadoPedido === "ERROR") {
            setErrorPago("Wompi reportó un error al procesar el pago. Puedes revisar el pedido desde tu perfil.");
            return;
          }

          setErrorPago(
            resPago?.mensajeRespuesta ||
              "No fue posible confirmar el resultado del pago. Consulta el estado del pedido desde tu perfil."
          );
        } catch (err) {
          setErrorPago(err.message || "No se pudo confirmar el pago con el servidor.");
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
    <div className="app-shell-page">
      <AppTopbar />

      <main id="contenido-principal" tabIndex={-1} className="app-hero">
        <div className="app-decor app-decor--1" />
        <div className="app-decor app-decor--2" />
        <div className="app-content catalogo-pagina">
          <BotonRegresar />

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
                  {["Todos", ...categoriasDe(productos)].map((categoria) => (
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
                          {manejaStock(producto) ? (
                            <span className={`producto-stock ${producto.stock <= 0 ? "producto-stock--agotado" : producto.stock <= 5 ? "producto-stock--bajo" : ""}`}>
                              {producto.stock <= 0 ? "Agotado" : producto.stock <= 5 ? `Últimas ${producto.stock} unidades` : `${producto.stock} unidades disponibles`}
                            </span>
                          ) : (
                            <span className="producto-stock">Servicio disponible</span>
                          )}
                          <button
                            type="button"
                            className="catalogo-btn"
                            disabled={manejaStock(producto) && (producto.stock <= 0 || (carrito[producto.id] || 0) >= producto.stock)}
                            onClick={() => cambiarCantidad(producto.id, 1)}
                          >
                            {manejaStock(producto) && producto.stock <= 0 ? "Agotado" : manejaStock(producto) && (carrito[producto.id] || 0) >= producto.stock ? "Stock máximo" : <>Añadir<span className="catalogo-btn__extra"> al carrito</span></>}
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

              <aside className="carrito" id="carrito-resumen" aria-label="Carrito de compras">
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

              {unidades > 0 && (
                <a className="carrito-flotante" href="#carrito-resumen">
                  <span>
                    Ver carrito <b>{unidades}</b>
                  </span>
                  <strong>{formatearCOP(total)}</strong>
                </a>
              )}
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
                El valor final de tu pedido se confirma al momento de pagar.
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