import { request } from "./client";

export const fetchProductos = (token = null, admin = false) =>
  request(admin ? "/productos/admin" : "/productos", token ? { token } : {});

export const crearProducto = (token, body) =>
  request("/productos", { method: "POST", body, token });

export const actualizarProducto = (token, id, body) =>
  request(`/productos/${id}`, { method: "PATCH", body, token });

export const eliminarProducto = (token, id) =>
  request(`/productos/${id}`, { method: "DELETE", token });
