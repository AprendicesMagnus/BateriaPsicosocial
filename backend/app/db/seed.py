from app.core.config import get_settings
from app.core.crypto import hash_password
from app.db.session import SessionLocal
from app.models.survey import Baremo, CuestionarioVersion, Dimension, Pregunta, Recomendacion
from app.models.user import Permiso, Rol, RolPermiso, Usuario

PERMISOS = [
    ("GESTIONAR_USUARIOS", "Gestionar usuarios", "USUARIOS"),
    ("GESTIONAR_ORGANIZACIONES", "Gestionar organizaciones", "ORGANIZACIONES"),
    ("GESTIONAR_CUESTIONARIOS", "Gestionar cuestionarios", "CUESTIONARIOS"),
    ("GESTIONAR_EVALUACIONES", "Gestionar evaluaciones", "EVALUACIONES"),
    ("VER_RESULTADOS", "Ver resultados de evaluaciones", "EVALUACIONES"),
    ("GENERAR_INFORMES", "Generar informes", "INFORMES"),
    ("VER_AUDITORIA", "Ver registros de auditoría", "AUDITORIA"),
]

ROLES = {
    "ADMINISTRADOR": {
        "nombre": "Administrador",
        "descripcion": "Administra el sistema en su totalidad.",
        "permisos": [codigo for codigo, _, _ in PERMISOS],
    },
    "EVALUADOR_SST": {
        "nombre": "Evaluador SST",
        "descripcion": "Aplica y gestiona evaluaciones de riesgo psicosocial.",
        "permisos": [
            "GESTIONAR_CUESTIONARIOS",
            "GESTIONAR_EVALUACIONES",
            "VER_RESULTADOS",
            "GENERAR_INFORMES",
        ],
    },
    "TRABAJADOR": {
        "nombre": "Trabajador",
        "descripcion": "Responde las evaluaciones asignadas.",
        "permisos": [],
    },
}


def sembrar_permisos(db) -> dict[str, Permiso]:
    codigos_validos = {codigo for codigo, _, _ in PERMISOS}
    # Eliminar relaciones de permisos obsoletos
    obsoletos = db.query(Permiso).filter(~Permiso.codigo.in_(codigos_validos)).all()
    for obs in obsoletos:
        db.query(RolPermiso).filter(RolPermiso.permiso_id == obs.id).delete()
        db.delete(obs)
    db.flush()

    existentes = {p.codigo: p for p in db.query(Permiso).all()}
    for codigo, nombre, modulo in PERMISOS:
        if codigo not in existentes:
            permiso = Permiso(codigo=codigo, nombre=nombre, modulo=modulo)
            db.add(permiso)
            existentes[codigo] = permiso
        else:
            existentes[codigo].nombre = nombre
            existentes[codigo].modulo = modulo
    db.flush()
    return existentes


def sembrar_roles(db, permisos: dict[str, Permiso]) -> dict[str, Rol]:
    existentes = {r.codigo: r for r in db.query(Rol).all()}
    for codigo, datos in ROLES.items():
        rol = existentes.get(codigo)
        if rol is None:
            rol = Rol(
                codigo=codigo,
                nombre=datos["nombre"],
                descripcion=datos["descripcion"],
                es_sistema=True,
                activo=True,
            )
            db.add(rol)
            db.flush()
            existentes[codigo] = rol
        asignados = {rp.permiso_id for rp in rol.permisos}
        for codigo_permiso in datos["permisos"]:
            permiso = permisos[codigo_permiso]
            if permiso.id not in asignados:
                db.add(RolPermiso(rol_id=rol.id, permiso_id=permiso.id))
    db.flush()
    return existentes


def sembrar_administrador(db, roles: dict[str, Rol]) -> None:
    settings = get_settings()
    existente = db.query(Usuario).filter(Usuario.email == settings.admin_email.lower()).first()
    if existente:
        return
    admin = Usuario(
        nombre=settings.admin_nombre,
        apellido=settings.admin_apellido,
        email=settings.admin_email.lower(),
        password_hash=hash_password(settings.admin_password),
        rol_id=roles["ADMINISTRADOR"].id,
        estado="ACTIVO",
        email_verificado=True,
    )
    db.add(admin)


def sembrar_cuestionario_brp(db) -> CuestionarioVersion:
    codigo_cuestionario = "BRP_FORMA_A"
    version_existente = (
        db.query(CuestionarioVersion)
        .filter(CuestionarioVersion.codigo == codigo_cuestionario, CuestionarioVersion.vigente.is_(True))
        .first()
    )
    if version_existente:
        # Asegurar que las recomendaciones estén sembradas en dimensiones existentes
        for dim in version_existente.dimensiones:
            if not dim.recomendaciones:
                _sembrar_recs_dimension(db, dim)
        db.flush()
        return version_existente

    version = CuestionarioVersion(
        codigo=codigo_cuestionario,
        nombre="Cuestionario de Factores de Riesgo Psicosocial Intralaboral - Forma A",
        numero_version=1,
        descripcion="Instrumento oficial conforme a la Resolución 2764 de 2022 del Ministerio del Trabajo de Colombia.",
        vigente=True,
    )
    db.add(version)
    db.flush()

    baremos_estandar = [
        ("SIN_RIESGO", 0.0, 19.9, 1),
        ("BAJO", 20.0, 39.9, 2),
        ("MEDIO", 40.0, 59.9, 3),
        ("ALTO", 60.0, 79.9, 4),
        ("MUY_ALTO", 80.0, 100.0, 5),
    ]

    dimensiones_data = [
        {
            "codigo": "LIDERAZGO",
            "nombre": "Características del liderazgo y relaciones sociales en el trabajo",
            "dominio": "Liderazgo y relaciones sociales en el trabajo",
            "orden": 1,
            "preguntas": [
                {
                    "codigo": "P1",
                    "enunciado": "Mi jefe me brinda retroalimentación clara y constructiva sobre mi desempeño laboral.",
                    "orden": 1,
                    "inversa": True,
                },
                {
                    "codigo": "P2",
                    "enunciado": "Mi jefe distribuye las cargas de trabajo de manera justa y equitativa.",
                    "orden": 2,
                    "inversa": True,
                },
                {
                    "codigo": "P3",
                    "enunciado": "Se presentan conflictos o discusiones frecuentes con mi jefe inmediato.",
                    "orden": 3,
                    "inversa": False,
                },
            ],
        },
        {
            "codigo": "CONTROL",
            "nombre": "Control sobre el trabajo y autonomía",
            "dominio": "Control sobre el trabajo",
            "orden": 2,
            "preguntas": [
                {
                    "codigo": "P4",
                    "enunciado": "Puedo tomar decisiones sobre el ritmo al que realizo mis actividades laborales.",
                    "orden": 4,
                    "inversa": True,
                },
                {
                    "codigo": "P5",
                    "enunciado": "En mi trabajo tengo oportunidades continuas para aplicar mis habilidades y destrezas.",
                    "orden": 5,
                    "inversa": True,
                },
                {
                    "codigo": "P6",
                    "enunciado": "Las normas o procedimientos internos me impiden proponer mejoras a mi trabajo.",
                    "orden": 6,
                    "inversa": False,
                },
            ],
        },
        {
            "codigo": "DEMANDAS",
            "nombre": "Demandas cuantitativas y de carga mental del trabajo",
            "dominio": "Demandas del trabajo",
            "orden": 3,
            "preguntas": [
                {
                    "codigo": "P7",
                    "enunciado": "Por la cantidad de trabajo que tengo, debo quedarme tiempo adicional después de mi jornada.",
                    "orden": 7,
                    "inversa": False,
                },
                {
                    "codigo": "P8",
                    "enunciado": "Debo atender tareas urgentes con un tiempo límite muy corto que me genera tensión.",
                    "orden": 8,
                    "inversa": False,
                },
                {
                    "codigo": "P9",
                    "enunciado": "El trabajo me exige mantener un esfuerzo de concentración mental continuo y agotador.",
                    "orden": 9,
                    "inversa": False,
                },
            ],
        },
    ]

    for d_data in dimensiones_data:
        dim = Dimension(
            version_id=version.id,
            codigo=d_data["codigo"],
            nombre=d_data["nombre"],
            dominio=d_data["dominio"],
            orden=d_data["orden"],
        )
        db.add(dim)
        db.flush()

        for p_data in d_data["preguntas"]:
            preg = Pregunta(
                dimension_id=dim.id,
                codigo=p_data["codigo"],
                enunciado=p_data["enunciado"],
                orden=p_data["orden"],
                inversa=p_data["inversa"],
                valor_minimo=1,
                valor_maximo=5,
            )
            db.add(preg)

        for nivel, minimo, maximo, orden in baremos_estandar:
            bar = Baremo(
                dimension_id=dim.id,
                nivel=nivel,
                minimo=minimo,
                maximo=maximo,
                orden=orden,
            )
            db.add(bar)

        # Sembrar recomendaciones por dimensión y nivel de riesgo conforme Res. 2764 de 2022
        _sembrar_recs_dimension(db, dim)

    db.flush()
    return version


def _sembrar_recs_dimension(db, dim: Dimension) -> None:
    recomendaciones_data = {
        "LIDERAZGO": {
            "SIN_RIESGO": ("Mantenimiento de prácticas saludables de liderazgo", "Mantener los canales abiertos de comunicación y promover el reconocimiento constante del desempeño."),
            "BAJO": ("Fomento de liderazgo participativo", "Realizar capacitaciones periódicas en comunicación asertiva y retroalimentación constructiva para supervisores."),
            "MEDIO": ("Desarrollo de competencias directivas", "Implementar talleres de resolución pacífica de conflictos y justicia en la distribución de tareas."),
            "ALTO": ("Intervención prioritaria en estilos de mando", "Realizar diagnóstico cualitativo del clima de equipo, mediación de relaciones y coaching directivo."),
            "MUY_ALTO": ("Intervención urgente en supervisión y clima laboral", "Reestructurar esquemas de supervisión, auditoría de clima laboral e intervención psicosocial individual prioritaria."),
        },
        "CONTROL": {
            "SIN_RIESGO": ("Promoción de la autonomía laboral", "Fomentar la proactividad del trabajador y su participación voluntaria en comités de mejora continua."),
            "BAJO": ("Estimulación del desarrollo de habilidades", "Brindar oportunidades de capacitación continua y flexibilidad en la organización del ritmo de trabajo."),
            "MEDIO": ("Revisión de autonomía y margen de decisión", "Evaluar procedimientos para otorgar mayor participación al trabajador en la planificación de sus jornadas."),
            "ALTO": ("Rediseño de puestos de trabajo", "Ampliar los márgenes de decisión técnica y eliminar normas rígidas que limiten la iniciativa del empleado."),
            "MUY_ALTO": ("Reestructuración de procesos y empoderamiento", "Rediseñar puestos críticos otorgando autonomía efectiva y eliminando cuellos de botella burocráticos."),
        },
        "DEMANDAS": {
            "SIN_RIESGO": ("Monitoreo preventivo de ritmos de trabajo", "Mantener el seguimiento preventivo de horarios y distribución de cargas de trabajo."),
            "BAJO": ("Gestión del tiempo y pausas activas", "Promover programas sistemáticos de pausas activas y organización eficiente del tiempo."),
            "MEDIO": ("Optimización de flujos y cargas", "Revisar asignación de objetivos para prevenir tiempos suplementarios o jornadas extendidas no programadas."),
            "ALTO": ("Intervención en carga mental y cuantitativa", "Redistribuir tareas críticas, establecer protocolos claros de prioridades y brindar manejo del estrés."),
            "MUY_ALTO": ("Reajuste operacional urgente y salud ocupacional", "Ajustar objetivos cuantitativos, evaluar ampliación de apoyo operativo e iniciar monitoreo de estrés ocupacional."),
        },
    }

    dim_recs = recomendaciones_data.get(dim.codigo, {})
    prio_map = {"SIN_RIESGO": 5, "BAJO": 4, "MEDIO": 3, "ALTO": 2, "MUY_ALTO": 1}
    for nivel, (tit, desc) in dim_recs.items():
        db.add(
            Recomendacion(
                dimension_id=dim.id,
                nivel=nivel,
                titulo=tit,
                descripcion=desc,
                prioridad=prio_map.get(nivel, 3),
            )
        )


def ejecutar_seed() -> None:
    db = SessionLocal()
    try:
        permisos = sembrar_permisos(db)
        roles = sembrar_roles(db, permisos)
        sembrar_administrador(db, roles)
        sembrar_cuestionario_brp(db)
        db.commit()
        print("Seed aplicado correctamente (roles, permisos, admin y cuestionario BRP).")
    finally:
        db.close()


if __name__ == "__main__":
    ejecutar_seed()

