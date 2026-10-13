// Constantes y formatos compartidos por Reportes.jsx y Respuestas.jsx

// Colores y textos de cada nivel de riesgo (mismos que usa CuestionarioTrabajador)
export const NIVELES = {
  SIN_RIESGO: { bg: "#DEF7EC", text: "#03543F", label: "Sin riesgo" },
  BAJO: { bg: "#E1EFFE", text: "#1E40AF", label: "Riesgo bajo" },
  MEDIO: { bg: "#FEF08A", text: "#713F12", label: "Riesgo medio" },
  ALTO: { bg: "#FDBA74", text: "#9A3412", label: "Riesgo alto" },
  MUY_ALTO: { bg: "#FCA5A5", text: "#991B1B", label: "Riesgo muy alto" },
};

// Texto y estilo del estado de la encuesta del trabajador (EvaluacionParticipante.estado)
export const ESTADOS_ENCUESTA = {
  COMPLETADA: { label: "Completada", clase: "reportes-status--listo" },
  EN_PROGRESO: { label: "En progreso", clase: "reportes-status--progreso" },
  PENDIENTE: { label: "Pendiente", clase: "reportes-status--restringido" },
};

// Nombre corto de cada instrumento para etiquetas y pestañas
export const NOMBRES_INSTRUMENTO = {
  FICHA_DATOS: "Ficha de datos",
  ESTRES: "Estrés",
  EXTRALABORAL: "Extralaboral",
  INTRALABORAL_A: "Intralaboral A",
  INTRALABORAL_B: "Intralaboral B",
};

// "2026-09-29T16:05:18-05:00" -> "29/09/2026, 4:05 p. m."
export function formatearFecha(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("es-CO", { dateStyle: "short", timeStyle: "short" });
}

// Texto de cada valor guardado, por instrumento (mismos mapas que usan los cuestionarios al enviar)
const ETIQUETAS_INTRALABORAL = { 4: "Siempre", 3: "Casi siempre", 2: "Algunas veces", 1: "Casi nunca", 0: "Nunca" };
const ETIQUETAS_RESPUESTA = {
  ESTRES: { 4: "Siempre", 3: "Casi siempre", 2: "A veces", 1: "Nunca" },
  EXTRALABORAL: { 5: "Siempre", 4: "Casi siempre", 3: "Algunas veces", 2: "Casi nunca", 1: "Nunca" },
  INTRALABORAL_A: ETIQUETAS_INTRALABORAL,
  INTRALABORAL_B: ETIQUETAS_INTRALABORAL,
};

export function textoRespuesta(codigoInstrumento, valor) {
  if (valor === null || valor === undefined || valor === "") return "—";
  if (typeof valor === "boolean") return valor ? "Sí" : "No";
  return ETIQUETAS_RESPUESTA[codigoInstrumento]?.[valor] ?? String(valor);
}

// Minúsculas y sin tildes, para que "maria" encuentre "María"
export function normalizar(texto) {
  return (texto || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
}

export function iniciales(nombre) {
  return (nombre || "?")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0].toUpperCase())
    .join("");
}
