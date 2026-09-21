const LETRAS = "A-Za-zÁÉÍÓÚÜÑáéíóúüñ";

export const MAX_NIT_LENGTH = 11;
export const MAX_EMAIL_LENGTH = 180;
export const MAX_PASSWORD_LENGTH = 72;
export const MAX_NOMBRE_LENGTH = 100;
export const MAX_RAZON_SOCIAL_LENGTH = 180;
export const MAX_LUGAR_LENGTH = 80;
export const MAX_CARGO_LENGTH = 100;
export const MAX_AREA_LENGTH = 120;
export const MAX_TELEFONO_LENGTH = 10;
export const MAX_TRABAJADORES_LENGTH = 7;
export const MAX_IDENTIFICACION_LENGTH = 15;
export const MAX_UUID_LENGTH = 36;
export const MAX_TARJETA_LENGTH = 23;
export const MAX_VENCIMIENTO_LENGTH = 5;
export const MAX_CVV_LENGTH = 4;
export const MAX_CANTIDAD_LENGTH = 6;
export const MAX_CODIGO_LENGTH = 6;

function limpiarEspacios(valor) {
  return valor.replace(/ {2,}/g, " ").replace(/^ /, "");
}

export function filtrarNombrePersona(valor, max = 100) {
  if (!valor) return "";
  return limpiarEspacios(valor.replace(new RegExp(`[^${LETRAS} ]`, "g"), "")).slice(0, max);
}

export function nombrePersonaValido(valor, max = 100) {
  if (!valor) return false;
  const limpio = valor.trim();
  return limpio.length >= 2 && limpio.length <= max && new RegExp(`^[${LETRAS}]+( [${LETRAS}]+)*$`).test(limpio);
}

export function filtrarLugar(valor, max = 80) {
  if (!valor) return "";
  return limpiarEspacios(valor.replace(new RegExp(`[^${LETRAS} .-]`, "g"), "")).slice(0, max);
}

export function lugarValido(valor) {
  if (!valor) return false;
  const limpio = valor.trim();
  return limpio.length >= 2 && limpio.length <= 80 && new RegExp(`^[${LETRAS}][${LETRAS} .-]*$`).test(limpio);
}

export function filtrarTextoLibre(valor, max = 100) {
  if (!valor) return "";
  return limpiarEspacios(valor.replace(new RegExp(`[^${LETRAS}0-9 .,&'()/-]`, "g"), "")).slice(0, max);
}

export function textoLibreValido(valor, max = 100) {
  if (!valor) return false;
  const limpio = valor.trim();
  const letras = limpio.match(new RegExp(`[${LETRAS}]`, "g")) || [];
  return (
    limpio.length >= 2 &&
    limpio.length <= max &&
    letras.length >= 2 &&
    new RegExp(`^[${LETRAS}0-9][${LETRAS}0-9 .,&'()/-]*$`).test(limpio)
  );
}

export function soloDigitos(valor, max) {
  if (!valor && valor !== 0) return "";
  const str = String(valor).replace(/\D/g, "");
  return typeof max === "number" ? str.slice(0, max) : str;
}

export function enteroEnRango(valor, minimo, maximo) {
  if (typeof valor === "number") {
    return Number.isInteger(valor) && valor >= minimo && valor <= maximo;
  }
  if (typeof valor !== "string" || !/^\d+$/.test(valor.trim())) return false;
  const numero = Number(valor.trim());
  return numero >= minimo && numero <= maximo;
}

export function normalizarEmail(valor) {
  if (!valor) return "";
  return valor.trim().toLowerCase().slice(0, 180);
}

export function emailValido(valor) {
  if (!valor) return false;
  const limpio = valor.trim();
  return limpio.length <= 180 && /^[^@\s]+@[^@\s]+\.[^@\s]{2,}$/.test(limpio);
}

export function passwordValida(valor) {
  if (!valor) return false;
  return (
    valor.length >= 8 &&
    new TextEncoder().encode(valor).length <= 72 &&
    /[a-z]/.test(valor) &&
    /[A-Z]/.test(valor) &&
    /\d/.test(valor)
  );
}

export const TEXTO_AYUDA_PASSWORD = "Mínimo 8 caracteres, con mayúsculas, minúsculas y números (máximo 72).";

export function formatearNit(valor) {
  if (!valor) return "";
  const limpio = String(valor).replace(/[^\d-]/g, "");
  const partes = limpio.split("-");
  const base = partes[0].replace(/\D/g, "").slice(0, 9);
  if (partes.length > 1) {
    const dv = partes.slice(1).join("").replace(/\D/g, "").slice(0, 1);
    return `${base}-${dv}`;
  }
  if (base.length > 9) {
    return `${base.slice(0, 9)}-${base.slice(9, 10)}`;
  }
  return base;
}

export function formatearVencimiento(value) {
  if (!value) return "";
  const digits = String(value).replace(/\D/g, "").slice(0, 4);
  if (!digits) return "";
  if (digits.length <= 2) return digits;
  return `${digits.slice(0, 2)}/${digits.slice(2, 4)}`;
}

export function formatearTarjeta(value) {
  if (!value) return "";
  const digits = String(value).replace(/\D/g, "").slice(0, 19);
  return digits.replace(/(.{4})/g, "$1 ").trim();
}

export function vencimientoValido(valor, hoy = new Date()) {
  if (!valor) return false;
  const coincidencia = /^(0[1-9]|1[0-2])\/(\d{2})$/.exec(valor.trim());
  if (!coincidencia) return false;
  const finDeMes = new Date(2000 + Number(coincidencia[2]), Number(coincidencia[1]), 0, 23, 59, 59);
  return finDeMes >= hoy;
}

export function uuidValido(valor) {
  if (!valor) return false;
  return /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/.test(valor.trim());
}
