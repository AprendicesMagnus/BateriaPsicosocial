"""Resumen mensual de la bateria por correo para Jefe, Administrador y Responsable SST.

Solo contiene conteos agregados (sin nombres, areas ni datos individuales). El detalle de riesgo
se muestra unicamente si la empresa tiene el minimo de personas para el anonimato; la cifra es la
misma que usa el Dashboard (dimensiones en nivel alto o muy alto, acumulado).
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.crypto import utcnow
from app.models.evaluation import Evaluacion, EvaluacionParticipante, Notificacion
from app.models.organization import Organizacion
from app.models.user import Rol, Usuario
from app.services.correo import enviar_correo
from app.services.indicadores import obtener_resumen_indicadores
from app.services.notificaciones import notificar

TIPO_NOTIFICACION = "RESUMEN_MENSUAL"
ROLES_DESTINO = ("JEFE", "ADMINISTRADOR", "RESPONSABLE_SST")
ZONA_COLOMBIA = timezone(timedelta(hours=-5))  # Colombia no cambia de horario
DIAS_DE_ENVIO = 7  # el resumen se envia solo durante los primeros dias del mes
MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


def _periodo_anterior(ahora: datetime) -> tuple[datetime, datetime, datetime]:
    """Devuelve (ahora en hora de Colombia, inicio del mes anterior, inicio del mes actual)."""
    local = ahora.astimezone(ZONA_COLOMBIA)
    inicio_actual = local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    inicio_anterior = (inicio_actual - timedelta(days=1)).replace(day=1)
    return local, inicio_anterior, inicio_actual


def _nombre_periodo(inicio: datetime) -> str:
    return f"{MESES[inicio.month - 1]} de {inicio.year}"


def _empresas_del_usuario(db: Session, usuario: Usuario) -> list[Organizacion]:
    if usuario.rol.codigo == "RESPONSABLE_SST":
        organizacion = usuario.organizacion
        return [organizacion] if organizacion is not None and organizacion.activa else []
    return (
        db.query(Organizacion)
        .filter(Organizacion.creada_por_id == usuario.id, Organizacion.activa.is_(True))
        .order_by(Organizacion.nombre)
        .all()
    )


def _datos_empresa(db: Session, organizacion: Organizacion, inicio: datetime, fin: datetime) -> dict:
    completados_mes = (
        db.query(func.count(EvaluacionParticipante.id))
        .join(Evaluacion, Evaluacion.id == EvaluacionParticipante.evaluacion_id)
        .filter(
            Evaluacion.organizacion_id == organizacion.id,
            EvaluacionParticipante.estado == "COMPLETADA",
            EvaluacionParticipante.fecha_fin >= inicio,
            EvaluacionParticipante.fecha_fin < fin,
        )
        .scalar()
        or 0
    )
    pendientes = (
        db.query(func.count(EvaluacionParticipante.id))
        .join(Evaluacion, Evaluacion.id == EvaluacionParticipante.evaluacion_id)
        .filter(
            Evaluacion.organizacion_id == organizacion.id,
            Evaluacion.estado == "EN_CURSO",
            EvaluacionParticipante.estado != "COMPLETADA",
        )
        .scalar()
        or 0
    )
    resumen = obtener_resumen_indicadores(db, organizacion.id)
    participacion = resumen["participacion"]
    riesgo = resumen["distribucionRiesgo"]
    return {
        "completadosMes": completados_mes,
        "pendientes": pendientes,
        "completados": participacion["totalCompletados"],
        "asignados": participacion["totalAsignados"],
        "participacion": participacion["tasaPorcentaje"],
        "dimensionesAltas": None if riesgo is None else riesgo["ALTO"] + riesgo["MUY_ALTO"],
    }


def _texto_empresa(nombre_empresa: str, datos: dict) -> str:
    lineas = [
        f"Empresa: {nombre_empresa}",
        f"- Cuestionarios completados en el mes: {datos['completadosMes']}",
        (
            f"- Cuestionarios completados en total: {datos['completados']} de "
            f"{datos['asignados']} asignados ({datos['participacion']} %)"
        ),
        f"- Personas con la evaluación pendiente: {datos['pendientes']}",
    ]
    if datos["dimensionesAltas"] is None:
        minimo = get_settings().min_grupo_anonimato
        lineas.append(
            "- Dimensiones en nivel alto o muy alto (acumulado): no se muestra para proteger el "
            f"anonimato (se requieren al menos {minimo} personas con cuestionarios completados)."
        )
    else:
        lineas.append(f"- Dimensiones en nivel alto o muy alto (acumulado): {datos['dimensionesAltas']}")
    return "\n".join(lineas)


def enviar_resumenes_mensuales(db: Session, ahora: datetime | None = None) -> dict:
    """Envia, durante los primeros dias del mes, el resumen del mes anterior (una sola vez por persona).
    Una empresa sin actividad en el mes y sin pendientes no aparece; si ninguna empresa de la persona
    tiene actividad, no se envia nada."""
    ahora = ahora or utcnow()
    local, inicio, fin = _periodo_anterior(ahora)
    if local.day > DIAS_DE_ENVIO:
        return {"usuariosRevisados": 0, "resumenesEnviados": 0}

    periodo = _nombre_periodo(inicio)
    titulo = f"Resumen de {periodo}"
    usuarios = (
        db.query(Usuario)
        .filter(
            Usuario.estado == "ACTIVO",
            Usuario.es_invitado.is_(False),
            Usuario.rol.has(Rol.codigo.in_(ROLES_DESTINO)),
        )
        .all()
    )
    enviados = 0

    for usuario in usuarios:
        ya_enviado = (
            db.query(Notificacion.id)
            .filter(
                Notificacion.usuario_id == usuario.id,
                Notificacion.tipo == TIPO_NOTIFICACION,
                Notificacion.titulo == titulo,
            )
            .first()
        )
        if ya_enviado:
            continue

        secciones = []
        total_mes = 0
        for organizacion in _empresas_del_usuario(db, usuario):
            datos = _datos_empresa(db, organizacion, inicio, fin)
            if datos["completadosMes"] == 0 and datos["pendientes"] == 0:
                continue
            total_mes += datos["completadosMes"]
            secciones.append(_texto_empresa(organizacion.nombre, datos))
        if not secciones:
            continue

        cuerpo = (
            f"Hola {usuario.nombre},\n\n"
            f"Este es el resumen de {periodo} de la batería de riesgo psicosocial.\n\n"
            + "\n\n".join(secciones)
            + "\n\nIngresa a la plataforma para ver el detalle en el Dashboard. "
            "Este resumen solo incluye conteos y no contiene datos individuales."
        )
        notificar(
            db,
            usuario_id=usuario.id,
            tipo=TIPO_NOTIFICACION,
            titulo=titulo,
            mensaje=(
                f"Resumen de la batería de {periodo}: {total_mes} cuestionario(s) completado(s) en el mes. "
                "Revisa el detalle en el Dashboard."
            ),
            commit=False,
        )
        enviar_correo(usuario.email, f"Resumen mensual de la batería - {periodo}", cuerpo)
        enviados += 1

    db.commit()
    return {"usuariosRevisados": len(usuarios), "resumenesEnviados": enviados}
