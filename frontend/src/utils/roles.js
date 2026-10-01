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

// Usuario limitado que crea un Jefe/Administrador al registrar una empresa:
// solo puede usar el módulo de Reportes (y ver/editar su perfil).
export const ROL_SOLO_REPORTES = "RESPONSABLE_SST";
export const RUTAS_PERMITIDAS_SOLO_REPORTES = ["/reportes", "/perfil"];

export function rutaPermitidaParaRol(rol, pathname) {
  if (rol !== ROL_SOLO_REPORTES) return true;
  return RUTAS_PERMITIDAS_SOLO_REPORTES.some(
    (ruta) => pathname === ruta || pathname.startsWith(`${ruta}/`)
  );
}

// Página a la que se envía a cada rol justo después de iniciar sesión.
export const rutaInicial = (rol) => (rol === ROL_SOLO_REPORTES ? "/reportes" : "/Inicio");
