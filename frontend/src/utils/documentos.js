// Tipos de documento que acepta el Centro de ayuda y formato de tamaño.
export const EXTENSIONES_DOCUMENTO = ["pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx"];
export const MAX_DOCUMENTO_MB = 10;

const ETIQUETAS = { pdf: "PDF", doc: "Word", docx: "Word", xls: "Excel", xlsx: "Excel", ppt: "PowerPoint", pptx: "PowerPoint" };

export const etiquetaTipoDocumento = (ext) => ETIQUETAS[String(ext || "").toLowerCase()] || String(ext || "").toUpperCase() || "Archivo";

export function formatearTamano(bytes) {
  if (!bytes && bytes !== 0) return "";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1).replace(".", ",")} MB`;
}
