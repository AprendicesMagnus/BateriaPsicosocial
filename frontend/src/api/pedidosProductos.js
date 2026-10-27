import { request } from "./client";

export const crearPedidoProductos = (token, items) =>
  request("/pedidos-productos", {
    method: "POST",
    body: { items },
    token,
  });

export const obtenerPedidoProductos = (token, id) =>
  request(`/pedidos-productos/${id}`, { token });

export const prepararCheckoutPedidoProductos = (token, id) =>
  request(`/pedidos-productos/${id}/wompi/checkout`, {
    method: "POST",
    token,
  });

export const confirmarPagoPedidoProductos = (token, pedidoId, wompiTransactionId) =>
  request("/pedidos-productos/pago", {
    method: "POST",
    body: { pedido_id: pedidoId, wompi_transaction_id: wompiTransactionId },
    token,
  });

export const cancelarPedidoProductos = (token, id) =>
  request(`/pedidos-productos/${id}/cancelar`, {
    method: "POST",
    token,
  });
