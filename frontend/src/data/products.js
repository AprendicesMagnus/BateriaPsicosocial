import { useCallback, useEffect, useState } from "react";
import { urlArchivo } from "../api/client";
import {
  actualizarProducto,
  crearProducto,
  eliminarProducto,
  fetchProductos,
} from "../api/productos";

export const CATEGORIAS_PRODUCTO = ["SST", "Tecnología"];

// Los servicios (es_servicio) no llevan inventario: siempre disponibles.
export const manejaStock = (producto) => !producto?.es_servicio;

// Categorías en uso: las base primero y luego las nuevas, en orden alfabético.
export const categoriasDe = (productos = []) => {
  const enUso = new Set(productos.map((p) => p.categoria).filter(Boolean));
  const base = CATEGORIAS_PRODUCTO.filter((c) => enUso.has(c));
  const extra = [...enUso].filter((c) => !CATEGORIAS_PRODUCTO.includes(c)).sort((a, b) => a.localeCompare(b, "es"));
  return [...base, ...extra];
};

export const formatearCOP = (valor) =>
  new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: "COP",
    maximumFractionDigits: 0,
  }).format(Number(valor) || 0);

function ilustracion() {
  const svg =
    `<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300" viewBox="0 0 400 300">` +
    `<rect width="400" height="300" fill="#eef1f6"/>` +
    `<text x="200" y="185" font-size="120" text-anchor="middle">📦</text></svg>`;
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
}

export const imagenDe = (producto) => urlArchivo(producto?.imagen_url) || ilustracion();

export function useProductos({ token = null, admin = false } = {}) {
  const [productos, setProductos] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");

  const recargar = useCallback(async () => {
    setCargando(true);
    setError("");
    try {
      const data = await fetchProductos(token, admin);
      setProductos(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err.message || "No se pudieron cargar los productos.");
    } finally {
      setCargando(false);
    }
  }, [token, admin]);

  useEffect(() => {
    recargar();
  }, [recargar]);

  const crear = useCallback(
    async (datos) => {
      const producto = await crearProducto(token, datos);
      setProductos((actuales) => [...actuales, producto]);
      return producto;
    },
    [token]
  );

  const actualizar = useCallback(
    async (id, datos) => {
      const producto = await actualizarProducto(token, id, datos);
      setProductos((actuales) =>
        actuales.map((actual) => (actual.id === id ? producto : actual))
      );
      return producto;
    },
    [token]
  );

  const eliminar = useCallback(
    async (id) => {
      await eliminarProducto(token, id);
      setProductos((actuales) => actuales.filter((producto) => producto.id !== id));
    },
    [token]
  );

  return {
    productos,
    cargando,
    error,
    crear,
    actualizar,
    eliminar,
    recargar,
  };
}
