"""Agrupaciones de roles reutilizables (evita repetir listas de códigos en cada servicio)."""

# Quienes gestionan una empresa: el Psicologo (EVALUADOR_SST) y el Responsable SST que un
# Jefe/Administrador crea al registrar la empresa. Mismos permisos, limitados a su empresa activa.
ROLES_EVALUADOR = frozenset({"EVALUADOR_SST", "RESPONSABLE_SST"})

# Roles de dirección de la empresa: consultan solo datos agregados y anonimizados.
ROLES_DIRECCION = frozenset({"JEFE", "ADMINISTRADOR"})
