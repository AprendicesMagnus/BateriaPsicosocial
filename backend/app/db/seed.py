from app.core.config import get_settings
from app.core.crypto import hash_password
from app.db.session import SessionLocal
from app.models.survey import Baremo, CuestionarioVersion, Dimension, Pregunta, Recomendacion
from app.models.user import Permiso, Rol, RolPermiso, Usuario
from app.db.intralaboral_oficial import sembrar_forma_intralaboral

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


def sembrar_todos_los_cuestionarios(db) -> dict[str, CuestionarioVersion]:
    """
    Siembra las 5 versiones de cuestionarios oficiales del sistema:
    1. FICHA_DATOS (19 ítems mixtos)
    2. ESTRES (31 ítems, Likert 1-4)
    3. EXTRALABORAL (31 ítems, Likert 1-5)
    4. INTRALABORAL_A (123 ítems, Likert 0-4 oficial)
    5. INTRALABORAL_B (97 ítems, Likert 0-4 oficial)
    """
    versiones = {}

    # 1. FICHA_DATOS
    v_ficha = db.query(CuestionarioVersion).filter(CuestionarioVersion.codigo == "FICHA_DATOS", CuestionarioVersion.vigente.is_(True)).first()
    if not v_ficha:
        v_ficha = CuestionarioVersion(
            codigo="FICHA_DATOS",
            nombre="Ficha de Datos Generales",
            numero_version=1,
            descripcion="Información sociodemográfica y ocupacional del trabajador.",
            vigente=True,
        )
        db.add(v_ficha)
        db.flush()
        dim_ficha = Dimension(
            version_id=v_ficha.id,
            codigo="DATOS_SOCIO_LABORALES",
            nombre="Datos Sociodemográficos y Ocupacionales",
            dominio="Ficha de Datos Generales",
            orden=1,
        )
        db.add(dim_ficha)
        db.flush()

        preguntas_ficha = [
            ("F1", "Nombre completo", 1, "TEXTO"),
            ("F2", "Sexo", 2, "SELECCION"),
            ("F3", "Año de nacimiento", 3, "ANNO"),
            ("F4", "Estado civil", 4, "SELECCION"),
            ("F5", "Último nivel de estudios que alcanzó", 5, "SELECCION"),
            ("F6", "Ocupación o profesión", 6, "TEXTO"),
            ("F7", "Lugar de residencia actual - Ciudad / Municipio", 7, "TEXTO"),
            ("F8", "Lugar de residencia actual - Departamento", 8, "TEXTO"),
            ("F9", "Estrato socioeconómico de la vivienda", 9, "SELECCION"),
            ("F10", "Tipo de vivienda", 10, "SELECCION"),
            ("F11", "Número de personas a cargo", 11, "ENTERO"),
            ("F12", "Lugar donde trabaja actualmente - Ciudad / Municipio", 12, "TEXTO"),
            ("F13", "Lugar donde trabaja actualmente - Departamento", 13, "TEXTO"),
            ("F14", "Antigüedad en la empresa", 14, "TEXTO"),
            ("F15", "Nombre del cargo", 15, "TEXTO"),
            ("F16", "Tipo de cargo", 16, "SELECCION"),
            ("F17", "Antigüedad en el cargo actual", 17, "TEXTO"),
            ("F18", "Área o departamento de trabajo", 18, "TEXTO"),
            ("F19", "Tipo de contrato laboral", 19, "SELECCION"),
            ("F20", "Horas de trabajo diarias", 20, "ENTERO"),
            ("F21", "Tipo de salario", 21, "SELECCION"),
        ]
        for cod, enun, ord_idx, tipo in preguntas_ficha:
            db.add(
                Pregunta(
                    dimension_id=dim_ficha.id,
                    codigo=cod,
                    enunciado=enun,
                    orden=ord_idx,
                    inversa=False,
                    valor_minimo=1,
                    valor_maximo=5,
                    tipo_respuesta=tipo,
                )
            )
        db.flush()
    versiones["FICHA_DATOS"] = v_ficha

    # 2. ESTRES (31 preguntas, escala 1-4)
    v_estres = db.query(CuestionarioVersion).filter(CuestionarioVersion.codigo == "ESTRES", CuestionarioVersion.vigente.is_(True)).first()
    if not v_estres:
        v_estres = CuestionarioVersion(
            codigo="ESTRES",
            nombre="Cuestionario para la Evaluación del Estrés",
            numero_version=1,
            descripcion="Instrumento para la evaluación de los síntomas de estrés (3ª versión). Escala de 4 puntos (1-4).",
            vigente=True,
        )
        db.add(v_estres)
        db.flush()
        dim_estres = Dimension(
            version_id=v_estres.id,
            codigo="SINTOMAS_ESTRES",
            nombre="Síntomas de Estrés",
            dominio="Evaluación del Estrés",
            orden=1,
        )
        db.add(dim_estres)
        db.flush()

        preguntas_estres_textos = [
            "Dolores en el cuello y espalda o tensión muscular.",
            "Problemas gastrointestinales, úlcera péptica, acidez, problemas digestivos o del colon.",
            "Problemas respiratorios.",
            "Dolor de cabeza.",
            "Trastornos del sueño como somnolencia durante el día o desvelo en la noche.",
            "Palpitaciones en el pecho o problemas cardíacos.",
            "Cambios fuertes del apetito.",
            "Problemas relacionados con la función de los órganos genitales (impotencia, frigidez).",
            "Dificultad en las relaciones familiares.",
            "Dificultad para permanecer quieto o dificultad para iniciar actividades.",
            "Dificultad en las relaciones con otras personas.",
            "Sensación de aislamiento y desinterés.",
            "Sentimiento de sobrecarga de trabajo.",
            "Dificultad para concentrarse, olvidos frecuentes.",
            "Aumento en el número de accidentes de trabajo.",
            "Sentimiento de frustración, de no haber hecho lo que se quería en la vida.",
            "Cansancio, tedio o desgano.",
            "Disminución del rendimiento en el trabajo o poca creatividad.",
            "Deseo de no asistir al trabajo.",
            "Bajo compromiso o poco interés con lo que se hace.",
            "Dificultad para tomar decisiones.",
            "Deseo de cambiar de empleo.",
            "Sentimiento de soledad y miedo.",
            "Sentimiento de irritabilidad, actitudes y pensamientos negativos.",
            "Sentimiento de angustia, preocupación o tristeza.",
            "Consumo de drogas para aliviar la tensión o los nervios.",
            'Sentimientos de que "no vale nada", o "no sirve para nada".',
            "Consumo de bebidas alcohólicas o café o cigarrillo.",
            "Sentimiento de que está perdiendo la razón.",
            "Comportamientos rígidos, obstinación o terquedad.",
            "Sensación de no poder manejar los problemas de la vida.",
        ]
        for idx, texto in enumerate(preguntas_estres_textos, start=1):
            db.add(
                Pregunta(
                    dimension_id=dim_estres.id,
                    codigo=f"EST_{idx}",
                    enunciado=texto,
                    orden=idx,
                    inversa=False,
                    valor_minimo=1,
                    valor_maximo=4,
                    tipo_respuesta="LIKERT",
                )
            )
        db.flush()
    versiones["ESTRES"] = v_estres

    # 3. EXTRALABORAL (31 preguntas, Likert 1-5)
    v_extra = db.query(CuestionarioVersion).filter(CuestionarioVersion.codigo == "EXTRALABORAL", CuestionarioVersion.vigente.is_(True)).first()
    if not v_extra:
        v_extra = CuestionarioVersion(
            codigo="EXTRALABORAL",
            nombre="Cuestionario de Factores Psicosociales Extralaborales",
            numero_version=1,
            descripcion="Evaluación de los factores psicosociales fuera del entorno laboral.",
            vigente=True,
        )
        db.add(v_extra)
        db.flush()
        dim_extra = Dimension(
            version_id=v_extra.id,
            codigo="CONDICIONES_EXTRALABORALES",
            nombre="Factores Extralaborales",
            dominio="Entorno Extralaboral",
            orden=1,
        )
        db.add(dim_extra)
        db.flush()

        preguntas_extra_textos = [
            "Es fácil trasportarme entre mi casa y el trabajo.",
            "Tengo que tomar varios medios de transporte para llegar a mi lugar de trabajo.",
            "Paso mucho tiempo viajando de ida y regreso al trabajo.",
            "Me trasporto cómodamente entre mi casa y el trabajo.",
            "La zona donde vivo es segura.",
            "En la zona donde vivo se presentan hurtos y mucha delincuencia.",
            "Desde donde vivo me es fácil llegar al centro médico donde me atienden.",
            "Cerca a mi vivienda las vías están en buenas condiciones.",
            "Cerca a mi vivienda encuentro fácilmente transporte.",
            "Las condiciones de mi vivienda son buenas.",
            "En mi vivienda hay servicios de agua y luz.",
            "Las condiciones de mi vivienda me permiten descansar cuando lo requiero.",
            "Las condiciones de mi vivienda me permiten sentirme cómodo.",
            "Me queda tiempo para actividades de recreación.",
            "Fuera del trabajo tengo tiempo suficiente para descansar.",
            "Tengo tiempo para atender mis asuntos personales y del hogar.",
            "Tengo tiempo para compartir con mi familia o amigos.",
            "Tengo buena comunicación con las personas cercanas.",
            "Las relaciones con mis amigos son buenas.",
            "Converso con personas cercanas sobre diferentes temas.",
            "Mis amigos están dispuestos a escucharme cuando tengo problemas.",
            "Cuento con el apoyo de mi familia cuando tengo problemas.",
            "Puedo hablar con personas cercanas sobre las cosas que me pasan.",
            "Mis problemas personales o familiares afectan mi trabajo.",
            "La relación con mi familia cercana es cordial.",
            "Mis problemas personales o familiares me quitan la energía que necesito para trabajar.",
            "Los problemas con mis familiares los resolvemos de manera amistosa.",
            "Mis problemas personales o familiares afectan mis relaciones en el trabajo.",
            "El dinero que ganamos en el hogar alcanza para cubrir los gastos básicos.",
            "Tengo otros compromisos económicos que afectan mucho el presupuesto familiar.",
            "En mi hogar tenemos deudas difíciles de pagar.",
        ]
        for idx, texto in enumerate(preguntas_extra_textos, start=1):
            db.add(
                Pregunta(
                    dimension_id=dim_extra.id,
                    codigo=f"EXT_{idx}",
                    enunciado=texto,
                    orden=idx,
                    inversa=False,
                    valor_minimo=1,
                    valor_maximo=5,
                    tipo_respuesta="LIKERT",
                )
            )
        db.flush()
    versiones["EXTRALABORAL"] = v_extra

    # 4 y 5. INTRALABORAL_A (123 preguntas, 19 dimensiones) e INTRALABORAL_B
    # (97 preguntas, 16 dimensiones). Estructura oficial completa: dimensiones,
    # dominios y total del cuestionario, con factores de transformacion y
    # baremos reales tomados de las Tablas 21-34 del Manual del Ministerio de
    # la Proteccion Social (2010), via docs/referencia_intralaboral_A_B.json
    # (generado y verificado contra el PDF fuente en scripts/generar_referencia_intralaboral.py).
    v_intra_a = sembrar_forma_intralaboral(db, "forma_A")
    versiones["INTRALABORAL_A"] = v_intra_a

    v_intra_b = sembrar_forma_intralaboral(db, "forma_B")
    versiones["INTRALABORAL_B"] = v_intra_b

    baremos_estandar = [
        ("SIN_RIESGO", 0.0, 19.9, 1),
        ("BAJO", 20.0, 39.9, 2),
        ("MEDIO", 40.0, 59.9, 3),
        ("ALTO", 60.0, 79.9, 4),
        ("MUY_ALTO", 80.0, 100.0, 5),
    ]
    for v in versiones.values():
        for dim in v.dimensiones:
            if not dim.baremos:
                for b_nivel, b_min, b_max, b_orden in baremos_estandar:
                    db.add(Baremo(dimension_id=dim.id, nivel=b_nivel, minimo=b_min, maximo=b_max, orden=b_orden))
    db.flush()

    return versiones


def ejecutar_seed() -> None:
    db = SessionLocal()
    try:
        permisos = sembrar_permisos(db)
        roles = sembrar_roles(db, permisos)
        sembrar_administrador(db, roles)
        sembrar_cuestionario_brp(db)
        sembrar_todos_los_cuestionarios(db)
        db.commit()
        print("Seed aplicado correctamente (roles, permisos, admin, BRP y los 5 instrumentos reales).")
    finally:
        db.close()


if __name__ == "__main__":
    ejecutar_seed()