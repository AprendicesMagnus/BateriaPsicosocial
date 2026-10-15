export const formatearPrecio = (valor) =>
  new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 }).format(valor ?? 0);

export const etiquetaRango = (min, max) =>
  max == null ? `${min} baterías en adelante` : `${min} a ${max} baterías`;
