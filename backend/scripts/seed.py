# ==============================================================================
# DEPRECATED / LEGACY: Este script está OBSOLETO.
# La fuente de verdad actual para el seed de datos es: app/db/seed.py
# No utilizar este archivo en producción ni desarrollo.
# ==============================================================================
import sys
from pathlib import Path

if __name__ == "__main__" and "--force-legacy" not in sys.argv:
    print(
        "ERROR: scripts/seed.py está DEPRECATED y desalineado con los routers actuales.\n"
        "Usa en su lugar: python -m app.db.seed"
    )
    sys.exit(1)

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.crypto import hash_password
from app.db.session import SessionLocal
from app.models.catalog import Permiso, Rol, RolPermiso
from app.models.user import Usuario

settings = get_settings()

PERMISOS_BASE = [
    # Módulo Usuarios
    ("VER_USUARIOS", "Ver listado y perfiles de usuarios", "usuarios"),
    ("GESTIONAR_USUARIOS", "Crear, editar y desactivar usuarios", "usuarios"),
    # Módulo Roles
    ("VER_ROLES", "Ver catálogo de roles y permisos", "roles"),
    ("GESTIONAR_ROLES", "Crear y modificar roles", "roles"),
    # Módulo Organizaciones
    ("VER_ORGANIZACIONES", "Ver empresas y áreas", "organizaciones"),
    ("GESTIONAR_ORGANIZACIONES", "Crear y editar empresas y áreas", "organizaciones"),
    # Módulo Cuestionarios
    ("VER_CUESTIONARIOS", "Ver cuestionarios, preguntas y baremos", "cuestionarios"),
    ("GESTIONAR_CUESTIONARIOS", "Crear versiones y editar cuestionarios", "cuestionarios"),
    # Módulo Evaluaciones
    ("VER_EVALUACIONES", "Ver evaluaciones asignadas", "evaluaciones"),
    ("GESTIONAR_EVALUACIONES", "Crear, iniciar y finalizar evaluaciones", "evaluaciones"),
    ("RESPONDER_EVALUACION", "Responder cuestionarios asignados", "evaluaciones"),
    ("VER_RESULTADOS", "Ver resultados y reportes de evaluaciones", "evaluaciones"),
    # Módulo Auditoría
    ("VER_AUDITORIA", "Consultar logs de auditoría", "auditoria"),
    # Módulo Notificaciones
    ("VER_NOTIFICACIONES", "Ver y gestionar notificaciones", "notificaciones"),
]

ROLES_BASE = {
    "ADMINISTRADOR": {
        "nombre": "Administrador del Sistema",
        "descripcion": "Acceso total y administración de la plataforma",
        "es_sistema": True,
        "permisos": [p[0] for p in PERMISOS_BASE],
    },
    "EVALUADOR_SST": {
        "nombre": "Evaluador SST",
        "descripcion": "Gestión de evaluaciones psicosociales y consulta de resultados",
        "es_sistema": True,
        "permisos": [
            "VER_USUARIOS",
            "VER_ORGANIZACIONES",
            "VER_CUESTIONARIOS",
            "VER_EVALUACIONES",
            "GESTIONAR_EVALUACIONES",
            "VER_RESULTADOS",
            "VER_NOTIFICACIONES",
        ],
    },
    "TRABAJADOR": {
        "nombre": "Trabajador",
        "descripcion": "Participante en evaluaciones psicosociales",
        "es_sistema": True,
        "permisos": [
            "RESPONDER_EVALUACION",
            "VER_RESULTADOS",
            "VER_NOTIFICACIONES",
        ],
    },
}


def ejecutar_seed(db: Session) -> None:
    print("Iniciando seed de datos base...")

    # 1. Crear permisos
    permisos_map = {}
    for codigo, nombre, modulo in PERMISOS_BASE:
        permiso = db.query(Permiso).filter(Permiso.codigo == codigo).first()
        if not permiso:
            permiso = Permiso(codigo=codigo, nombre=nombre, modulo=modulo)
            db.add(permiso)
            db.flush()
            print(f"  [+] Permiso creado: {codigo}")
        permisos_map[codigo] = permiso

    # 2. Crear roles y asociar permisos
    roles_map = {}
    for codigo, data in ROLES_BASE.items():
        rol = db.query(Rol).filter(Rol.codigo == codigo).first()
        if not rol:
            rol = Rol(
                codigo=codigo,
                nombre=data["nombre"],
                descripcion=data["descripcion"],
                es_sistema=data["es_sistema"],
                activo=True,
            )
            db.add(rol)
            db.flush()
            print(f"  [+] Rol creado: {codigo}")
        roles_map[codigo] = rol

        # Asignar permisos
        permisos_actuales = {rp.permiso.codigo for rp in rol.permisos}
        for perm_cod in data["permisos"]:
            if perm_cod not in permisos_actuales and perm_cod in permisos_map:
                rp = RolPermiso(rol_id=rol.id, permiso_id=permisos_map[perm_cod].id)
                db.add(rp)
        db.flush()

    # 3. Crear usuario administrador inicial
    admin_email = settings.admin_email.lower().strip()
    admin_usuario = db.query(Usuario).filter(Usuario.email == admin_email).first()
    if not admin_usuario:
        admin_usuario = Usuario(
            nombre=settings.admin_nombre,
            apellido=settings.admin_apellido,
            email=admin_email,
            password_hash=hash_password(settings.admin_password),
            rol_id=roles_map["ADMINISTRADOR"].id,
            estado="ACTIVO",
            email_verificado=True,
        )
        db.add(admin_usuario)
        db.flush()
        print(f"  [+] Usuario administrador creado: {admin_email}")
    else:
        print(f"  [*] Usuario administrador ya existe: {admin_email}")

    db.commit()
    print("Seed completado exitosamente.")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        ejecutar_seed(db)
    finally:
        db.close()
