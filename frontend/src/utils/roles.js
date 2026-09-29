// Etiquetas visibles de cada rol. La clave es el código interno que devuelve el backend.
// Nota: "EVALUADOR_SST" es el código interno del rol que se muestra como "Psicologo".
export const ROL_LABEL = {
  SUPER_ADMINISTRADOR: "Super Administrador",
  ADMINISTRADOR: "Administrador",
  JEFE: "Jefe",
  EVALUADOR_SST: "Psicologo",
};

// Roles que la persona puede elegir por sí misma al registrarse (select y pantalla de Google).
export const ROLES_REGISTRO = [
  { value: "JEFE", label: "Jefe" },
  { value: "ADMINISTRADOR", label: "Administrador" },
  { value: "EVALUADOR_SST", label: "Psicologo" },
];

export const etiquetaRol = (codigo) => ROL_LABEL[codigo] ?? codigo ?? "";
