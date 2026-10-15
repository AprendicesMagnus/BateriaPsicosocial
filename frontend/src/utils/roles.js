// Etiquetas visibles de cada rol. La clave es el código interno que devuelve el backend.
// Nota: "EVALUADOR_SST" es el código interno del rol que se muestra como "Psicologo".
export const ROL_LABEL = {
  SUPER_ADMINISTRADOR: "Super Administrador",
  ADMINISTRADOR: "Administrador",
  JEFE: "Jefe",
  EVALUADOR_SST: "Psicologo",
  RESPONSABLE_SST: "Responsable SST",
};

// Roles que la persona puede elegir por sí misma al registrarse (select y pantalla de Google).
export const ROLES_REGISTRO = [
  { value: "JEFE", label: "Jefe" },
  { value: "ADMINISTRADOR", label: "Administrador" },
  { value: "EVALUADOR_SST", label: "Psicologo" },
];

export const etiquetaRol = (codigo) => ROL_LABEL[codigo] ?? codigo ?? "";

// Responsable SST: usuario que un Jefe/Administrador crea al registrar una empresa.
// Entra por el Dashboard y puede usar todo su contenido (cuestionarios, reportes, respuestas,
// enlaces) dentro de SU empresa. No ve el módulo de empresas, la tienda/pago ni el panel de administración.
export const ROL_RESPONSABLE = "RESPONSABLE_SST";
export const RUTAS_BLOQUEADAS_RESPONSABLE = [
  "/inicio",
  "/mis-empresas",
  "/crear-empresa",
  "/verificar-nit",
  "/pago",
  "/panel",
];

// Quienes gestionan una empresa y ven el Dashboard completo (Psicologo y Responsable SST).
export const ROLES_EVALUADOR = ["EVALUADOR_SST", ROL_RESPONSABLE];
export const esEvaluador = (rol) => ROLES_EVALUADOR.includes(rol);

export function rutaPermitidaParaRol(rol, pathname) {
  if (rol !== ROL_RESPONSABLE) return true;
  const ruta = pathname.toLowerCase();
  return !RUTAS_BLOQUEADAS_RESPONSABLE.some((bloqueada) => ruta === bloqueada || ruta.startsWith(`${bloqueada}/`));
}

// Página a la que se envía a cada rol justo después de iniciar sesión.
export const rutaInicial = (rol) => (rol === ROL_RESPONSABLE ? "/dashboard" : "/Inicio");

export const esSuperAdmin = (rol) => rol === "SUPER_ADMINISTRADOR";
