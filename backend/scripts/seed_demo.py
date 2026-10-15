"""
Siembra datos de demostración para la Batería de Riesgo Psicosocial.

Uso:
    cd backend
    python scripts/seed_demo.py --email <correo>
    python scripts/seed_demo.py --email <correo> --borrar
"""

import argparse
import os
import random
import sys
import uuid
from datetime import datetime, timezone

# Permite importar los módulos del proyecto cuando el script se ejecuta desde la
# carpeta backend/ directamente.
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.crypto import hash_password
from app.core.encryption import cifrar_json
from app.db.session import SessionLocal
from app.models.evaluation import (
    Consentimiento,
    Evaluacion,
    EvaluacionInstrumento,
    EvaluacionParticipante,
    Informe,
    ParticipanteInstrumento,
    Respuesta,
    ResultadoDimension,
)
from app.models.organization import Area, Organizacion
from app.models.survey import CuestionarioVersion, Dimension, Pregunta
from app.models.user import Rol, Usuario

# ---------------------------------------------------------------------------
# Constantes de demostración
# ---------------------------------------------------------------------------

PREFIJO = "[DEMO]"
NOMBRE_EVALUACION = "[DEMO] Evaluación de riesgo psicosocial 2026"
NOMBRE_AREAS = {
    "operaciones": "[DEMO] Operaciones",
    "administracion": "[DEMO] Administración",
    "ventas": "[DEMO] Ventas",
}

N_PARTICIPANTES = {
    "operaciones": 7,
    "administracion": 6,
    "ventas": 3,
}

NIVELES = ["SIN_RIESGO", "BAJO", "MEDIO", "ALTO", "MUY_ALTO"]

RANGO_POR_NIVEL = {
    "SIN_RIESGO": (0.0, 19.9),
    "BAJO": (20.0, 39.9),
    "MEDIO": (40.0, 59.9),
    "ALTO": (60.0, 79.9),
    "MUY_ALTO": (80.0, 100.0),
}

# Opciones válidas de la Ficha de Datos (fuente: Fichadatosgenerales.jsx)
OPCIONES_SEXO = ["Masculino", "Femenino"]
OPCIONES_ESTADO_CIVIL = [
    "Soltero (a)", "Casado (a)", "Unión libre",
    "Separado (a)", "Divorciado (a)",
]
OPCIONES_ESTUDIOS = [
    "Bachillerato completo",
    "Técnico / tecnológico completo",
    "Profesional completo",
    "Post-grado completo",
]
OPCIONES_ESTRATO = ["2", "3", "4"]
OPCIONES_VIVIENDA = ["Propia", "En arriendo", "Familiar"]
OPCIONES_TIPO_CARGO = [
    "Jefatura - tiene personal a cargo",
    "Profesional, analista, técnico, tecnólogo",
    "Auxiliar, asistente administrativo, asistente técnico",
    "Operario, operador, ayudante, servicios generales",
]
OPCIONES_CONTRATO = [
    "Término indefinido",
    "Temporal de 1 año o más",
    "Prestación de servicios",
]
OPCIONES_SALARIO = [
    "Fijo (diario, semanal, quincenal o mensual)",
    "Una parte fija y otra variable",
]
OPCIONES_ANTIGUEDAD = [
    "menos de 1 año", "2", "3", "5", "8", "10",
]


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _puntaje_para_nivel(rng: random.Random, nivel: str) -> float:
    lo, hi = RANGO_POR_NIVEL[nivel]
    return round(rng.uniform(lo, hi), 2)


def _nivel_dimension_operaciones(rng: random.Random, dim_codigo: str) -> str:
    """
    Para Operaciones: LIDERAZGO y DEMANDAS concentran ALTO/MUY_ALTO.
    CONTROL también tiene riesgo elevado.
    """
    if dim_codigo == "LIDERAZGO":
        return rng.choice(["ALTO", "ALTO", "MUY_ALTO", "MUY_ALTO", "ALTO"])
    if dim_codigo == "DEMANDAS":
        return rng.choice(["MUY_ALTO", "ALTO", "MUY_ALTO", "ALTO", "ALTO"])
    if dim_codigo == "CONTROL":
        return rng.choice(["ALTO", "MEDIO", "ALTO", "MUY_ALTO", "MEDIO"])
    return rng.choice(["SIN_RIESGO", "BAJO", "MEDIO", "BAJO", "MEDIO"])


def _nivel_dimension_administracion(rng: random.Random, dim_codigo: str) -> str:
    """
    Para Administración: riesgo menor, predomina SIN_RIESGO y BAJO.
    """
    if dim_codigo == "LIDERAZGO":
        return rng.choice(["BAJO", "MEDIO", "BAJO", "SIN_RIESGO", "MEDIO"])
    if dim_codigo == "DEMANDAS":
        return rng.choice(["MEDIO", "BAJO", "MEDIO", "ALTO", "BAJO"])
    return rng.choice(["SIN_RIESGO", "BAJO", "SIN_RIESGO", "BAJO", "MEDIO"])


def _nivel_dimension_ventas(rng: random.Random, dim_codigo: str) -> str:
    return rng.choice(["BAJO", "MEDIO", "SIN_RIESGO", "BAJO"])


# ---------------------------------------------------------------------------
# Verificación
# ---------------------------------------------------------------------------

def _obtener_usuario(db: Session, email: str) -> Usuario | None:
    return db.query(Usuario).filter(Usuario.email == email.lower().strip()).first()


def _preguntas_ficha(db: Session) -> dict[str, Pregunta]:
    """Devuelve un dict {codigo: Pregunta} con todas las preguntas de FICHA_DATOS."""
    version_ficha = (
        db.query(CuestionarioVersion)
        .filter(CuestionarioVersion.codigo == "FICHA_DATOS")
        .first()
    )
    if version_ficha is None:
        return {}
    resultado = {}
    for dim in version_ficha.dimensiones:
        for p in dim.preguntas:
            resultado[p.codigo] = p
    return resultado


def _version_brp(db: Session) -> CuestionarioVersion | None:
    return (
        db.query(CuestionarioVersion)
        .filter(CuestionarioVersion.codigo == "BRP_FORMA_A", CuestionarioVersion.vigente.is_(True))
        .first()
    )


def _ya_existe_demo(db: Session, organizacion_id: uuid.UUID) -> bool:
    return (
        db.query(Evaluacion)
        .filter(
            Evaluacion.organizacion_id == organizacion_id,
            Evaluacion.nombre.like(f"{PREFIJO}%"),
        )
        .first()
    ) is not None


# ---------------------------------------------------------------------------
# Creación
# ---------------------------------------------------------------------------

def _crear_trabajador(
    db: Session,
    organizacion_id: uuid.UUID,
    area_id: uuid.UUID,
    rol_paciente: Rol,
    indice: int,
    area_slug: str,
    rng: random.Random,
) -> Usuario:
    hex_corto = uuid.uuid4().hex[:8]
    email = f"demo_{area_slug}_{indice}_{hex_corto}@demo.bps"
    num_doc = str(rng.randint(10_000_000, 99_999_999))

    trabajador = Usuario(
        nombre=f"[DEMO] Trabajador {area_slug.capitalize()} {indice + 1}",
        apellido="Demostración",
        email=email,
        password_hash=hash_password(uuid.uuid4().hex + "Aa1"),
        rol_id=rol_paciente.id,
        estado="ACTIVO",
        email_verificado=True,
        organizacion_id=organizacion_id,
        area_id=area_id,
        numero_identificacion=num_doc,
        es_invitado=True,
    )
    db.add(trabajador)
    return trabajador


def _crear_respuestas_ficha(
    db: Session,
    participante: EvaluacionParticipante,
    preguntas_ficha: dict[str, Pregunta],
    rng: random.Random,
    area_nombre: str,
) -> None:
    """Crea las respuestas de la Ficha de Datos para el participante."""

    sexo = rng.choice(OPCIONES_SEXO)
    anno_nacimiento = str(rng.randint(1965, 2002))
    estado_civil = rng.choice(OPCIONES_ESTADO_CIVIL)
    estudios = rng.choice(OPCIONES_ESTUDIOS)
    estrato = rng.choice(OPCIONES_ESTRATO)
    vivienda = rng.choice(OPCIONES_VIVIENDA)
    tipo_cargo = rng.choice(OPCIONES_TIPO_CARGO)
    antiguedad = rng.choice(OPCIONES_ANTIGUEDAD)
    tipo_contrato = rng.choice(OPCIONES_CONTRATO)
    tipo_salario = rng.choice(OPCIONES_SALARIO)

    # Mapa: codigo_pregunta -> valor a guardar
    valores = {
        "F2": sexo,
        "F3": anno_nacimiento,
        "F4": estado_civil,
        "F5": estudios,
        "F9": estrato,
        "F14": tipo_cargo,
        "F16": area_nombre,
        "F19": tipo_contrato,
        "F21": tipo_salario,
        # Campos adicionales para completar el registro
        "F1": f"Trabajador Demo {rng.randint(100, 999)}",
        "F6": "Cargo Demo",
        "F7": "Neiva",
        "F8": vivienda,
        "F10": str(rng.randint(0, 3)),
        "F11": "Neiva",
        "F12": antiguedad,
        "F13": "Cargo Demo",
        "F15": antiguedad,
        "F17": tipo_contrato,
        "F18": str(rng.choice([8, 9, 10])),
        "F20": str(rng.choice([8, 9, 10])),
    }

    for codigo, valor in valores.items():
        pregunta = preguntas_ficha.get(codigo)
        if pregunta is None:
            continue
        db.add(
            Respuesta(
                participante_id=participante.id,
                pregunta_id=pregunta.id,
                valor_cifrado=cifrar_json(valor),
            )
        )


def _crear_resultados_dimension(
    db: Session,
    participante: EvaluacionParticipante,
    dimensiones: list[Dimension],
    area_slug: str,
    rng: random.Random,
) -> None:
    nivel_fn = {
        "operaciones": _nivel_dimension_operaciones,
        "administracion": _nivel_dimension_administracion,
        "ventas": _nivel_dimension_ventas,
    }.get(area_slug, _nivel_dimension_ventas)

    for dim in dimensiones:
        nivel = nivel_fn(rng, dim.codigo)
        puntaje_t = _puntaje_para_nivel(rng, nivel)
        puntaje_b = round(puntaje_t * (dim.factor_transformacion or 1.0) / 100, 2)

        db.add(
            ResultadoDimension(
                participante_id=participante.id,
                dimension_id=dim.id,
                puntaje_bruto=puntaje_b,
                puntaje_transformado=puntaje_t,
                nivel=nivel,
            )
        )


def sembrar(email: str) -> None:
    db: Session = SessionLocal()
    try:
        # 1. Obtener el usuario
        usuario = _obtener_usuario(db, email)
        if usuario is None:
            print(f"No se encontró ningún usuario con el correo '{email}'. No se creó nada.")
            return

        organizacion_id = usuario.organizacion_id
        if organizacion_id is None:
            print(
                f"El usuario '{email}' no tiene una organización activa. "
                "Seleccione una empresa en el perfil antes de ejecutar este script."
            )
            return

        org = db.query(Organizacion).filter(Organizacion.id == organizacion_id).first()
        n_areas = db.query(Area).filter(Area.organizacion_id == organizacion_id).count()
        n_evaluaciones = (
            db.query(Evaluacion)
            .filter(Evaluacion.organizacion_id == organizacion_id)
            .count()
        )

        print(f"Organización: {org.nombre}")
        print(f"  Áreas actuales: {n_areas}   |   Evaluaciones actuales: {n_evaluaciones}")

        # 2. Idempotencia
        if _ya_existe_demo(db, organizacion_id):
            print(
                "Ya existen datos de demostración para esta organización. "
                "Ejecute con --borrar para eliminarlos antes de volver a sembrar."
            )
            return

        # 3. Verificar cuestionarios
        preguntas_ficha = _preguntas_ficha(db)
        codigos_requeridos = {"F2", "F3", "F4", "F5", "F9", "F14", "F16", "F19", "F21"}
        faltantes = codigos_requeridos - set(preguntas_ficha.keys())
        if faltantes:
            print(
                "Faltan preguntas de FICHA_DATOS en la base de datos: "
                + ", ".join(sorted(faltantes))
                + ". Ejecute primero el seed de cuestionarios."
            )
            return

        version_brp = _version_brp(db)
        if version_brp is None:
            print(
                "No se encontró el cuestionario BRP_FORMA_A vigente. "
                "Ejecute primero el seed de cuestionarios."
            )
            return

        dimensiones_brp = sorted(version_brp.dimensiones, key=lambda d: d.orden)

        version_ficha = (
            db.query(CuestionarioVersion)
            .filter(CuestionarioVersion.codigo == "FICHA_DATOS")
            .first()
        )

        # 4. Rol TRABAJADOR
        rol_trabajador = db.query(Rol).filter(Rol.codigo == "TRABAJADOR").first()
        if rol_trabajador is None:
            print("El rol TRABAJADOR no está sembrado. Ejecute primero el seed de roles.")
            return

        rng = random.Random(2026)

        # 5. Crear todo en una única transacción ---------------------------------
        print("Creando datos de demostración...")

        # 5a. Áreas
        areas: dict[str, Area] = {}
        for slug, nombre_area in NOMBRE_AREAS.items():
            area = Area(
                organizacion_id=organizacion_id,
                nombre=nombre_area,
                activa=True,
            )
            db.add(area)
            db.flush()
            areas[slug] = area

        # 5b. Evaluación
        evaluacion = Evaluacion(
            organizacion_id=organizacion_id,
            evaluador_id=usuario.id,
            version_id=version_brp.id,
            nombre=NOMBRE_EVALUACION,
            estado="EN_CURSO",
            fecha_inicio=_utcnow(),
        )
        db.add(evaluacion)
        db.flush()

        # 5c. Instrumentos de la evaluación (FICHA_DATOS + BRP_FORMA_A)
        ei_ficha = EvaluacionInstrumento(
            evaluacion_id=evaluacion.id,
            version_id=version_ficha.id,
            orden=1,
            obligatorio=True,
        )
        ei_brp = EvaluacionInstrumento(
            evaluacion_id=evaluacion.id,
            version_id=version_brp.id,
            orden=2,
            obligatorio=True,
        )
        db.add(ei_ficha)
        db.add(ei_brp)
        db.flush()

        # 5d. Trabajadores y participantes
        total_creados = 0
        for slug, area in areas.items():
            n = N_PARTICIPANTES[slug]
            for i in range(n):
                trabajador = _crear_trabajador(
                    db, organizacion_id, area.id, rol_trabajador, i, slug, rng
                )
                db.flush()

                participante = EvaluacionParticipante(
                    evaluacion_id=evaluacion.id,
                    trabajador_id=trabajador.id,
                    estado="COMPLETADA",
                    notificado=False,
                    fecha_inicio=_utcnow(),
                    fecha_fin=_utcnow(),
                )
                db.add(participante)
                db.flush()

                # Sub-instrumentos del participante
                db.add(
                    ParticipanteInstrumento(
                        participante_id=participante.id,
                        instrumento_id=ei_ficha.id,
                        estado="COMPLETADA",
                        fecha_inicio=_utcnow(),
                        fecha_fin=_utcnow(),
                    )
                )
                db.add(
                    ParticipanteInstrumento(
                        participante_id=participante.id,
                        instrumento_id=ei_brp.id,
                        estado="COMPLETADA",
                        fecha_inicio=_utcnow(),
                        fecha_fin=_utcnow(),
                    )
                )

                # Consentimiento
                db.add(
                    Consentimiento(
                        participante_id=participante.id,
                        trabajador_id=trabajador.id,
                        aceptado=True,
                        texto_version="v1.0",
                        ip_origen="127.0.0.1",
                    )
                )

                # Respuestas de la Ficha de Datos
                _crear_respuestas_ficha(
                    db, participante, preguntas_ficha, rng, area.nombre
                )

                # Resultados por dimensión
                _crear_resultados_dimension(
                    db, participante, dimensiones_brp, slug, rng
                )

                total_creados += 1

        db.commit()

        print(f"Se crearon {len(areas)} áreas demo y {total_creados} participantes con resultados.")
        print(f"  Áreas:")
        for slug, area in areas.items():
            print(f"    - {area.nombre}  ({N_PARTICIPANTES[slug]} participantes)")
        print(f"  Evaluación: {evaluacion.nombre}")

        # 6. Verificación con los servicios reales --------------------------------
        print()
        print("Verificando con los servicios de indicadores...")
        _verificar(db, organizacion_id)

    except Exception as exc:
        db.rollback()
        print(f"Error durante la siembra. Se deshicieron todos los cambios.")
        raise exc
    finally:
        db.close()


def _verificar(db: Session, organizacion_id: uuid.UUID) -> None:
    from app.services.indicadores import (
        obtener_analisis_grupos,
        obtener_mapa_calor,
        obtener_priorizacion,
    )

    mapa = obtener_mapa_calor(db, organizacion_id=organizacion_id)
    areas_mapa = mapa.get("areas", [])
    areas_anonimizadas = sum(
        1 for a in areas_mapa
        if any(celda.get("anonimizado") for celda in a.get("celdas", {}).values())
    )
    print(f"Mapa de calor: {len(areas_mapa)} áreas  |  {areas_anonimizadas} con celdas anonimizadas")

    for a in areas_mapa:
        nombre = a.get("nombre", "")
        celdas = a.get("celdas", {})
        anonimizada = any(c.get("anonimizado") for c in celdas.values())
        estado = "ANONIMIZADA" if anonimizada else "visible"
        print(f"    {nombre}: {estado}")

    prio = obtener_priorizacion(db, organizacion_id=organizacion_id)
    dims_prio = prio.get("dimensiones", [])
    print(f"Priorización: {len(dims_prio)} dimensiones priorizadas")

    grupos_resp = obtener_analisis_grupos(db, organizacion_id=organizacion_id, variable="sexo")
    grupos = grupos_resp.get("grupos", [])
    ocultos = grupos_resp.get("gruposOcultos", 0)
    sin_dato = grupos_resp.get("sinDato", 0)
    print(f"Análisis por sexo: {len(grupos)} grupos visibles  |  {ocultos} ocultos  |  {sin_dato} sin dato")
    for g in grupos:
        print(f"    {g['nombre']}: {g['participantes']} participantes  ({g['porcentajeAltoMuyAlto']}% alto/muy alto)")


# ---------------------------------------------------------------------------
# Borrado
# ---------------------------------------------------------------------------

def borrar(email: str) -> None:
    db: Session = SessionLocal()
    try:
        usuario = _obtener_usuario(db, email)
        if usuario is None:
            print(f"No se encontró ningún usuario con el correo '{email}'.")
            return

        organizacion_id = usuario.organizacion_id
        if organizacion_id is None:
            print(f"El usuario '{email}' no tiene una organización activa.")
            return

        org = db.query(Organizacion).filter(Organizacion.id == organizacion_id).first()
        print(f"Organización: {org.nombre}")

        # Evaluaciones demo
        evaluaciones_demo = (
            db.query(Evaluacion)
            .filter(
                Evaluacion.organizacion_id == organizacion_id,
                Evaluacion.nombre.like(f"{PREFIJO}%"),
            )
            .all()
        )
        if not evaluaciones_demo:
            print("No hay datos de demostración para esta organización.")
            return

        n_respuestas = 0
        n_resultados = 0
        n_consentimientos = 0
        n_participantes = 0
        n_instrumentos_part = 0
        n_instrumentos_eval = 0
        n_informes = 0
        n_evaluaciones = 0
        n_trabajadores = 0
        n_areas = 0

        for evaluacion in evaluaciones_demo:
            participantes = (
                db.query(EvaluacionParticipante)
                .filter(EvaluacionParticipante.evaluacion_id == evaluacion.id)
                .all()
            )
            trabajadores_ids = [p.trabajador_id for p in participantes]

            for part in participantes:
                # Respuestas
                cnt = (
                    db.query(Respuesta)
                    .filter(Respuesta.participante_id == part.id)
                    .delete(synchronize_session=False)
                )
                n_respuestas += cnt

                # Resultados dimensión
                cnt = (
                    db.query(ResultadoDimension)
                    .filter(ResultadoDimension.participante_id == part.id)
                    .delete(synchronize_session=False)
                )
                n_resultados += cnt

                # Consentimientos
                cnt = (
                    db.query(Consentimiento)
                    .filter(Consentimiento.participante_id == part.id)
                    .delete(synchronize_session=False)
                )
                n_consentimientos += cnt

                # Sub-instrumentos del participante
                cnt = (
                    db.query(ParticipanteInstrumento)
                    .filter(ParticipanteInstrumento.participante_id == part.id)
                    .delete(synchronize_session=False)
                )
                n_instrumentos_part += cnt

            # Participantes
            cnt = (
                db.query(EvaluacionParticipante)
                .filter(EvaluacionParticipante.evaluacion_id == evaluacion.id)
                .delete(synchronize_session=False)
            )
            n_participantes += cnt

            # Informes
            informes = (
                db.query(Informe)
                .filter(Informe.evaluacion_id == evaluacion.id)
                .all()
            )
            for informe in informes:
                if informe.ruta_archivo and os.path.isfile(informe.ruta_archivo):
                    try:
                        os.remove(informe.ruta_archivo)
                    except OSError:
                        pass
                db.delete(informe)
                n_informes += 1

            # Instrumentos de la evaluación
            cnt = (
                db.query(EvaluacionInstrumento)
                .filter(EvaluacionInstrumento.evaluacion_id == evaluacion.id)
                .delete(synchronize_session=False)
            )
            n_instrumentos_eval += cnt

            # Evaluación
            db.delete(evaluacion)
            n_evaluaciones += 1

            # Trabajadores demo (solo los que tienen email demo)
            for tid in trabajadores_ids:
                trab = db.query(Usuario).filter(Usuario.id == tid).first()
                if trab and trab.email.endswith("@demo.bps"):
                    db.delete(trab)
                    n_trabajadores += 1

        db.flush()

        # Áreas demo
        areas_demo = (
            db.query(Area)
            .filter(
                Area.organizacion_id == organizacion_id,
                Area.nombre.like(f"{PREFIJO}%"),
            )
            .all()
        )
        for area in areas_demo:
            db.delete(area)
            n_areas += 1

        db.commit()

        print("Datos de demostración eliminados:")
        print(f"  Respuestas eliminadas:              {n_respuestas}")
        print(f"  Resultados de dimensión eliminados: {n_resultados}")
        print(f"  Consentimientos eliminados:         {n_consentimientos}")
        print(f"  Instrumentos de participante:       {n_instrumentos_part}")
        print(f"  Participantes eliminados:           {n_participantes}")
        print(f"  Informes eliminados:                {n_informes}")
        print(f"  Instrumentos de evaluación:         {n_instrumentos_eval}")
        print(f"  Evaluaciones eliminadas:            {n_evaluaciones}")
        print(f"  Trabajadores eliminados:            {n_trabajadores}")
        print(f"  Áreas eliminadas:                   {n_areas}")

    except Exception as exc:
        db.rollback()
        print("Error durante el borrado. Se deshicieron todos los cambios.")
        raise exc
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Entrada principal
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Siembra o elimina datos de demostración para la Batería Psicosocial."
    )
    parser.add_argument(
        "--email",
        required=True,
        help="Correo del usuario cuya organización activa se utilizará.",
    )
    parser.add_argument(
        "--borrar",
        action="store_true",
        help="Elimina los datos de demostración en lugar de crearlos.",
    )
    args = parser.parse_args()

    if args.borrar:
        borrar(args.email)
    else:
        sembrar(args.email)


if __name__ == "__main__":
    main()
