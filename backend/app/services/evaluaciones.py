from sqlalchemy.orm import Session, joinedload

from app.core.roles import ROLES_EVALUADOR
from app.core.crypto import utcnow
from app.core.encryption import cifrar_json, descifrar_json
from app.core.errors import AppError
from app.models.evaluation import (
    Consentimiento,
    Evaluacion,
    EvaluacionInstrumento,
    EvaluacionParticipante,
    Informe,
    ParticipanteInstrumento,
    Respuesta,
)
from app.models.survey import CuestionarioVersion, Dimension, Pregunta
from app.models.user import Usuario
from app.services.cuestionarios import version_vigente
from app.services.notificaciones import notificar
from app.services.tabulacion import tabular_participante

TEXTO_CONSENTIMIENTO = "CONSENTIMIENTO_BRP_V1"


def _evaluador_asignado(usuario: Usuario, evaluacion: Evaluacion) -> None:
    if usuario.rol.codigo == "SUPER_ADMINISTRADOR":
        return
    if evaluacion.evaluador_id != usuario.id:
        raise AppError(403, "Solo el evaluador SST asignado puede gestionar esta evaluación.")


def listar_evaluaciones(db: Session, actual: Usuario) -> list[dict]:
    query = db.query(Evaluacion).options(joinedload(Evaluacion.participantes))
    if actual.rol.codigo in ROLES_EVALUADOR:
        query = query.filter(Evaluacion.evaluador_id == actual.id)
    # PACIENTE: invitado del enlace público; igual que el trabajador, solo ve sus evaluaciones
    elif actual.rol.codigo in {"TRABAJADOR", "PACIENTE"}:
        query = query.join(EvaluacionParticipante).filter(EvaluacionParticipante.trabajador_id == actual.id)
    evaluaciones = query.order_by(Evaluacion.creado_en.desc()).all()
    return [_serializar_evaluacion(e) for e in evaluaciones]


def obtener_evaluacion(db: Session, evaluacion_id, actual: Usuario) -> dict:
    evaluacion = _get_evaluacion(db, evaluacion_id)
    _autorizar_consulta(actual, evaluacion)
    return _serializar_evaluacion(evaluacion, detalle=True)


def crear_evaluacion(db: Session, data, actual: Usuario) -> dict:
    if actual.rol.codigo not in {"SUPER_ADMINISTRADOR", *ROLES_EVALUADOR}:
        raise AppError(403, "No tiene permisos para crear evaluaciones.")
    if actual.rol.codigo in ROLES_EVALUADOR and actual.organizacion_id != data.organizacionId:
        raise AppError(403, "Solo puede crear evaluaciones de su organización.")
    version_id_explicito = data.versionId is not None
    version = (
        db.query(CuestionarioVersion).filter(CuestionarioVersion.id == data.versionId).first()
        if data.versionId
        else version_vigente(db)
    )
    evaluacion = Evaluacion(
        organizacion_id=data.organizacionId,
        evaluador_id=actual.id if actual.rol.codigo == "EVALUADOR_SST" else actual.id,
        version_id=version.id if version else None,
        nombre=data.nombre.strip(),
        estado="BORRADOR",
    )
    db.add(evaluacion)
    db.flush()

    participantes_creados = []
    for trabajador_id in data.trabajadoresIds:
        trabajador = db.query(Usuario).filter(Usuario.id == trabajador_id).first()
        if trabajador is None or trabajador.organizacion_id != data.organizacionId:
            raise AppError(400, "Hay trabajadores que no pertenecen a la organización.")
        part = EvaluacionParticipante(evaluacion_id=evaluacion.id, trabajador_id=trabajador_id)
        db.add(part)
        participantes_creados.append(part)
    db.flush()

    _inicializar_instrumentos_evaluacion(db, evaluacion, participantes_creados, version_id_explicito=version_id_explicito)

    db.commit()
    return obtener_evaluacion(db, evaluacion.id, actual)


def _inicializar_instrumentos_evaluacion(
    db: Session,
    evaluacion: Evaluacion,
    participantes: list[EvaluacionParticipante],
    version_id_explicito: bool = False,
):
    if version_id_explicito and evaluacion.version and evaluacion.version.codigo == "BRP_FORMA_A":
        return
    codigos = ["FICHA_DATOS", "ESTRES", "EXTRALABORAL"]
    eval_inst_map = {}
    for idx, codigo in enumerate(codigos, start=1):
        version = db.query(CuestionarioVersion).filter(CuestionarioVersion.codigo == codigo).first()
        if version:
            ei = EvaluacionInstrumento(
                evaluacion_id=evaluacion.id,
                version_id=version.id,
                orden=idx,
                obligatorio=True,
            )
            db.add(ei)
            db.flush()
            eval_inst_map[codigo] = ei

    for part in participantes:
        for codigo in codigos:
            ei = eval_inst_map.get(codigo)
            if ei:
                db.add(ParticipanteInstrumento(participante_id=part.id, instrumento_id=ei.id, estado="PENDIENTE"))


def iniciar_evaluacion(db: Session, evaluacion_id, actual: Usuario) -> dict:
    evaluacion = _get_evaluacion(db, evaluacion_id)
    _evaluador_asignado(actual, evaluacion)
    if evaluacion.estado == "FINALIZADA":
        raise AppError(400, "Una evaluación finalizada no puede reabrirse ni editarse.")
    evaluacion.estado = "EN_CURSO"
    evaluacion.fecha_inicio = utcnow()
    db.commit()
    return obtener_evaluacion(db, evaluacion.id, actual)


def notificar_participantes(db: Session, evaluacion_id, actual: Usuario, request=None) -> dict:
    evaluacion = _get_evaluacion(db, evaluacion_id)
    _evaluador_asignado(actual, evaluacion)
    if evaluacion.estado == "BORRADOR":
        iniciar_evaluacion(db, evaluacion_id, actual)
        evaluacion = _get_evaluacion(db, evaluacion_id)
    ahora = utcnow()
    for participante in evaluacion.participantes:
        if participante.notificado:
            continue
        participante.notificado = True
        participante.fecha_notificacion = ahora
        notificar(
            db,
            usuario_id=participante.trabajador_id,
            tipo="EVALUACION_PENDIENTE",
            titulo="Evaluación de riesgo psicosocial pendiente",
            mensaje="Tiene una evaluación asignada. Debe aceptar el consentimiento informado para iniciar el cuestionario.",
            evaluacion_id=evaluacion.id,
            commit=False,
        )
    db.commit()
    return obtener_evaluacion(db, evaluacion.id, actual)


def finalizar_evaluacion(db: Session, evaluacion_id, data, actual: Usuario) -> dict:
    evaluacion = _get_evaluacion(db, evaluacion_id)
    _evaluador_asignado(actual, evaluacion)
    if evaluacion.estado == "FINALIZADA":
        raise AppError(400, "Una evaluación finalizada no puede reabrirse ni editarse.")
    pendientes = [p for p in evaluacion.participantes if not p.notificado]
    if pendientes and not (data and data.justificacion):
        raise AppError(
            400,
            "No se puede finalizar una evaluación con trabajadores pendientes por notificar, salvo justificación registrada.",
        )
    evaluacion.estado = "FINALIZADA"
    evaluacion.fecha_fin = utcnow()
    evaluacion.justificacion_cierre = data.justificacion if data else None
    for p in evaluacion.participantes:
        if p.trabajador and p.trabajador.es_invitado is False:
            notificar(
                db,
                usuario_id=p.trabajador_id,
                tipo="EVALUACION_FINALIZADA",
                titulo="Evaluación finalizada",
                mensaje=f"La evaluación '{evaluacion.nombre}' fue finalizada.",
                evaluacion_id=evaluacion.id,
                commit=False,
            )
    db.commit()
    return obtener_evaluacion(db, evaluacion.id, actual)


def registrar_consentimiento(db: Session, evaluacion_id, actual: Usuario, ip: str | None) -> dict:
    participante = _participante_trabajador(db, evaluacion_id, actual)
    if participante.consentimiento:
        raise AppError(400, "El consentimiento no puede ser modificado ni eliminado una vez registrado.")
    consentimiento = Consentimiento(
        participante_id=participante.id,
        trabajador_id=actual.id,
        aceptado=True,
        texto_version=TEXTO_CONSENTIMIENTO,
        ip_origen=ip,
    )
    db.add(consentimiento)
    db.commit()
    return {
        "id": str(consentimiento.id),
        "registradoEn": consentimiento.registrado_en.isoformat(),
        "trabajadorId": str(actual.id),
    }


def obtener_instrumentos_participante(db: Session, evaluacion_id, actual: Usuario) -> list[dict]:
    participante = _participante_trabajador(db, evaluacion_id, actual)
    res = []
    for pi in sorted(participante.instrumentos_asignados, key=lambda i: i.instrumento.orden):
        res.append({
            "instrumentoId": str(pi.instrumento_id),
            "versionId": str(pi.instrumento.version_id),
            "codigo": pi.instrumento.version.codigo,
            "nombre": pi.instrumento.version.nombre,
            "orden": pi.instrumento.orden,
            "obligatorio": pi.instrumento.obligatorio,
            "estado": pi.estado,
        })
    return res


def guardar_ficha_datos(db: Session, evaluacion_id, data, actual: Usuario) -> dict:
    participante = _participante_trabajador(db, evaluacion_id, actual)
    if participante.consentimiento is None:
        raise AppError(403, "Debe aceptar el consentimiento informado antes de acceder a la Ficha de Datos Generales.")

    # 1. Guardar/actualizar respuestas de la Ficha en la tabla respuestas
    version_ficha = db.query(CuestionarioVersion).filter(CuestionarioVersion.codigo == "FICHA_DATOS").first()
    if version_ficha:
        preguntas_map = {p.codigo: p.id for dim in version_ficha.dimensiones for p in dim.preguntas}
        # Las claves son los nombres de campo de FichaDatosRequest (snake_case),
        # que es lo que devuelve data.model_dump().
        campo_pregunta_map = {
            "nombre_completo": "F1",
            "sexo": "F2",
            "ano_nacimiento": "F3",
            "estado_civil": "F4",
            "nivel_estudios": "F5",
            "ocupacion": "F6",
            "ciudad_residencia": "F7",
            "departamento_residencia": "F8",
            "estrato": "F9",
            "tipo_vivienda": "F10",
            "personas_a_cargo": "F11",
            "trabajo_ciudad": "F12",
            "trabajo_departamento": "F13",
            "antiguedad_empresa": "F14",
            "nombre_cargo": "F15",
            "cargo_tipo": "F16",
            "antiguedad_cargo": "F17",
            "area_departamento": "F18",
            "tipo_contrato": "F19",
            "horas_diarias": "F20",
            "salario_rango": "F21",
            "tiene_personal_a_cargo": "F22",
        }
        for campo, val in data.model_dump().items():
            if val is None:
                continue
            cod_p = campo_pregunta_map.get(campo)
            if cod_p and cod_p in preguntas_map:
                pid = preguntas_map[cod_p]
                existente = (
                    db.query(Respuesta)
                    .filter(Respuesta.participante_id == participante.id, Respuesta.pregunta_id == pid)
                    .first()
                )
                if existente:
                    existente.valor_cifrado = cifrar_json(val)
                    existente.actualizado_en = utcnow()
                else:
                    db.add(
                        Respuesta(
                            participante_id=participante.id,
                            pregunta_id=pid,
                            valor_cifrado=cifrar_json(val),
                        )
                    )

    # 2. Marcar el instrumento FICHA_DATOS como COMPLETADA
    inst_ficha = (
        db.query(ParticipanteInstrumento)
        .join(ParticipanteInstrumento.instrumento)
        .join(EvaluacionInstrumento.version)
        .filter(
            ParticipanteInstrumento.participante_id == participante.id,
            CuestionarioVersion.codigo == "FICHA_DATOS",
        )
        .first()
    )
    if inst_ficha:
        inst_ficha.estado = "COMPLETADA"
        inst_ficha.fecha_fin = utcnow()

    # 3. LÓGICA DE ASIGNACIÓN AUTOMÁTICA DE INTRALABORAL FORMA A vs FORMA B
    # Criterio de asignación: la respuesta del trabajador a la pregunta "¿Cuenta con personal
    # a cargo?" de la Ficha. Sí -> Forma A, No -> Forma B.
    codigo_target = None
    # Los enlaces restringidos a un solo cuestionario (p. ej. solo la Ficha) no reciben el
    # Intralaboral automático: el paciente solo debe responder lo que el psicólogo eligió.
    if participante.evaluacion.enlace_instrumento is None:
        es_forma_a = bool(data.tiene_personal_a_cargo)
        codigo_target = "INTRALABORAL_A" if es_forma_a else "INTRALABORAL_B"
        codigo_opuesto = "INTRALABORAL_B" if es_forma_a else "INTRALABORAL_A"

        # Garantizar que el trabajador NO tenga ambas formas del Intralaboral asignadas a la vez
        for pi in list(participante.instrumentos_asignados):
            if pi.instrumento.version.codigo == codigo_opuesto:
                db.delete(pi)
                db.flush()

        # Asignar el instrumento intralaboral correspondiente si no está asignado aún
        version_target = db.query(CuestionarioVersion).filter(CuestionarioVersion.codigo == codigo_target).first()
        if version_target:
            eval_inst_target = (
                db.query(EvaluacionInstrumento)
                .filter(
                    EvaluacionInstrumento.evaluacion_id == participante.evaluacion_id,
                    EvaluacionInstrumento.version_id == version_target.id,
                )
                .first()
            )
            if not eval_inst_target:
                eval_inst_target = EvaluacionInstrumento(
                    evaluacion_id=participante.evaluacion_id,
                    version_id=version_target.id,
                    orden=4,
                    obligatorio=True,
                )
                db.add(eval_inst_target)
                db.flush()

            pi_target = (
                db.query(ParticipanteInstrumento)
                .filter(
                    ParticipanteInstrumento.participante_id == participante.id,
                    ParticipanteInstrumento.instrumento_id == eval_inst_target.id,
                )
                .first()
            )
            if not pi_target:
                db.add(
                    ParticipanteInstrumento(
                        participante_id=participante.id,
                        instrumento_id=eval_inst_target.id,
                        estado="PENDIENTE",
                    )
                )

    # El paciente del enlace no tiene cuenta: su nombre sale de la Ficha para que el
    # psicólogo sepa quién respondió en "Encuestas realizadas"
    if actual.es_invitado and data.nombre_completo:
        actual.nombre = data.nombre_completo.strip()[:120]
        actual.apellido = ""

    ahora = utcnow()
    completado_total = False
    # Enlace restringido solo a la Ficha: al guardarla no queda ningún instrumento pendiente
    if participante.instrumentos_asignados and all(
        pi.estado == "COMPLETADA" for pi in participante.instrumentos_asignados
    ):
        db.flush()
        participante.estado = "COMPLETADA"
        participante.fecha_fin = ahora
        resultados = tabular_participante(db, participante)
        _alertar_riesgo(db, participante, resultados)
        evaluacion = participante.evaluacion
        if evaluacion.enlace_token and actual.es_invitado:
            evaluacion.estado = "FINALIZADA"
            evaluacion.fecha_fin = ahora
            evaluacion.justificacion_cierre = "Enlace cerrado automáticamente: el paciente terminó la batería."
        completado_total = True
    elif participante.estado == "PENDIENTE":
        participante.estado = "EN_PROGRESO"
        participante.fecha_inicio = ahora

    db.commit()
    return {
        "message": "Ficha de datos generales guardada correctamente.",
        "intralaboralAsignado": codigo_target,
        "completadoTotal": completado_total,
    }


def obtener_cuestionario_asignado(db: Session, evaluacion_id, actual: Usuario) -> dict:
    participante = _participante_trabajador(db, evaluacion_id, actual)
    if participante.consentimiento is None:
        raise AppError(403, "Debe aceptar el consentimiento informado antes de acceder al cuestionario.")

    version = None
    estado_cuestionario = participante.estado

    if participante.instrumentos_asignados:
        insts_ordenados = sorted(participante.instrumentos_asignados, key=lambda i: i.instrumento.orden)
        pi_pendiente = next((pi for pi in insts_ordenados if pi.estado != "COMPLETADA"), None)

        if pi_pendiente:
            version_id = pi_pendiente.instrumento.version_id
            version = (
                db.query(CuestionarioVersion)
                .options(joinedload(CuestionarioVersion.dimensiones).joinedload(Dimension.preguntas))
                .filter(CuestionarioVersion.id == version_id)
                .first()
            )
            estado_cuestionario = pi_pendiente.estado
        else:
            return {
                "evaluacionId": str(evaluacion_id),
                "estado": "COMPLETADA",
                "codigo": None,
                "nombre": None,
                "preguntas": [],
            }

    if not version and participante.evaluacion.version_id:
        version = (
            db.query(CuestionarioVersion)
            .options(joinedload(CuestionarioVersion.dimensiones).joinedload(Dimension.preguntas))
            .filter(CuestionarioVersion.id == participante.evaluacion.version_id)
            .first()
        )

    if not version:
        raise AppError(404, "No se encontró cuestionario asignado para esta evaluación.")

    respuestas = {str(r.pregunta_id): descifrar_json(r.valor_cifrado) for r in participante.respuestas}
    preguntas = []
    for dimension in sorted(version.dimensiones, key=lambda d: d.orden):
        for pregunta in sorted(dimension.preguntas, key=lambda p: p.orden):
            preguntas.append(
                {
                    "id": str(pregunta.id),
                    "codigo": pregunta.codigo,
                    "enunciado": pregunta.enunciado,
                    "orden": pregunta.orden,
                    "dimension": dimension.nombre,
                    "valorMinimo": pregunta.valor_minimo,
                    "valorMaximo": pregunta.valor_maximo,
                    "respuesta": respuestas.get(str(pregunta.id)),
                    # Filtro del que depende la pregunta ("CLIENTES" / "JEFE" / None); el frontend
                    # lo usa para reconstruir la respuesta "Sí" del filtro al recargar la página
                    "filtro": pregunta.filtro,
                }
            )
    return {
        "evaluacionId": str(evaluacion_id),
        "estado": estado_cuestionario,
        "codigo": version.codigo,
        "nombre": version.nombre,
        "preguntas": preguntas,
    }


def _versiones_permitidas(participante: EvaluacionParticipante) -> list:
    """Versiones de instrumento a las que puede responder el participante.

    Son las de sus instrumentos asignados. Solo cuando no tiene ninguno (flujo con
    un único cuestionario por evaluación) se usa la versión de la evaluación.
    """
    if participante.instrumentos_asignados:
        return [pi.instrumento.version_id for pi in participante.instrumentos_asignados]
    if participante.evaluacion.version_id:
        return [participante.evaluacion.version_id]
    return []


def guardar_respuesta(db: Session, evaluacion_id, data, actual: Usuario) -> dict:
    participante = _participante_trabajador(db, evaluacion_id, actual)
    if participante.consentimiento is None:
        raise AppError(403, "Debe aceptar el consentimiento informado antes de acceder al cuestionario.")
    if participante.estado == "COMPLETADA":
        raise AppError(400, "No se permite editar respuestas después de haber finalizado y enviado la evaluación.")
    pregunta = (
        db.query(Pregunta)
        .join(Dimension, Pregunta.dimension_id == Dimension.id)
        .filter(
            Pregunta.codigo == data.pregunta_codigo,
            Dimension.version_id.in_(_versiones_permitidas(participante)),
        )
        .first()
    )
    if pregunta is None:
        existe = db.query(Pregunta.id).filter(Pregunta.codigo == data.pregunta_codigo).first()
        if existe is not None:
            raise AppError(400, "La pregunta no pertenece a los instrumentos asignados al participante.")
        raise AppError(400, "La pregunta no existe.")
    # El valor puede ser número (Likert) o texto (ficha de datos). Solo se compara el rango
    # cuando es número; antes se comparaba siempre y un texto producía un error 500.
    if isinstance(data.valor, int):
        if data.valor < pregunta.valor_minimo or data.valor > pregunta.valor_maximo:
            raise AppError(400, "La respuesta no cumple con las condiciones del cuestionario.")
    elif pregunta.tipo_respuesta == "LIKERT":
        # Una pregunta Likert no acepta texto
        raise AppError(400, "Esta pregunta requiere un valor numérico.")
    existente = (
        db.query(Respuesta)
        .filter(Respuesta.participante_id == participante.id, Respuesta.pregunta_id == pregunta.id)
        .first()
    )
    if existente:
        existente.valor_cifrado = cifrar_json(data.valor)
        existente.actualizado_en = utcnow()
    else:
        db.add(
            Respuesta(
                participante_id=participante.id,
                pregunta_id=pregunta.id,
                valor_cifrado=cifrar_json(data.valor),
            )
        )
    if participante.estado == "PENDIENTE":
        participante.estado = "EN_PROGRESO"
        participante.fecha_inicio = utcnow()
    db.commit()
    return {"message": "Respuesta almacenada."}


def finalizar_cuestionario(db: Session, evaluacion_id, actual: Usuario, filtros: dict[str, bool] | None = None) -> dict:
    # filtros: respuestas del trabajador a las preguntas filtro, p. ej. {"CLIENTES": False, "JEFE": True}.
    # Sin filtros se exigen todas las preguntas del instrumento (comportamiento anterior).
    filtros = filtros or {}
    participante = _participante_trabajador(db, evaluacion_id, actual)
    if participante.estado == "COMPLETADA":
        raise AppError(400, "La evaluación ya fue finalizada.")

    pi_pendiente = None
    version = None

    if participante.instrumentos_asignados:
        insts_ordenados = sorted(participante.instrumentos_asignados, key=lambda i: i.instrumento.orden)
        pi_pendiente = next((pi for pi in insts_ordenados if pi.estado != "COMPLETADA"), None)
        if pi_pendiente:
            version = (
                db.query(CuestionarioVersion)
                .options(joinedload(CuestionarioVersion.dimensiones).joinedload(Dimension.preguntas))
                .filter(CuestionarioVersion.id == pi_pendiente.instrumento.version_id)
                .first()
            )

    if not version and participante.evaluacion.version_id:
        version = (
            db.query(CuestionarioVersion)
            .options(joinedload(CuestionarioVersion.dimensiones).joinedload(Dimension.preguntas))
            .filter(CuestionarioVersion.id == participante.evaluacion.version_id)
            .first()
        )

    if not version:
        raise AppError(404, "No se encontró cuestionario para finalizar.")

    todas = [p for d in version.dimensiones for p in d.preguntas]
    # Preguntas condicionales cuyo filtro se respondió "No": no se exigen
    omitidas = {p.id for p in todas if p.filtro and filtros.get(p.filtro) is False}
    if omitidas:
        # Si el trabajador respondió algunas y luego cambió el filtro a "No", se borran
        # para que no entren en la calificación
        db.query(Respuesta).filter(
            Respuesta.participante_id == participante.id,
            Respuesta.pregunta_id.in_(omitidas),
        ).delete(synchronize_session=False)
    # Solo se validan como obligatorias las preguntas que no fueron omitidas por un filtro
    esperadas = [p.id for p in todas if p.id not in omitidas]
    respondidas = {r.pregunta_id for r in participante.respuestas if r.pregunta_id not in omitidas}
    faltantes = [str(pid) for pid in esperadas if pid not in respondidas]
    if faltantes:
        raise AppError(400, "Existen preguntas pendientes por responder.", pendientes=faltantes)

    ahora = utcnow()

    if pi_pendiente:
        pi_pendiente.estado = "COMPLETADA"
        pi_pendiente.fecha_fin = ahora
        db.flush()

        restantes = [pi for pi in participante.instrumentos_asignados if pi.estado != "COMPLETADA"]
        if restantes:
            participante.estado = "EN_PROGRESO"
            db.commit()
            return {"message": f"Instrumento {version.nombre} finalizado.", "completadoTotal": False, "resultados": []}

    participante.estado = "COMPLETADA"
    participante.fecha_fin = ahora
    db.flush()
    resultados = tabular_participante(db, participante)
    _alertar_riesgo(db, participante, resultados)
    # El enlace del paciente es de un solo uso: al terminar la batería se cierra
    evaluacion = participante.evaluacion
    if evaluacion.enlace_token and actual.es_invitado:
        evaluacion.estado = "FINALIZADA"
        evaluacion.fecha_fin = ahora
        evaluacion.justificacion_cierre = "Enlace cerrado automáticamente: el paciente terminó la batería."
    db.commit()
    return {"message": "Evaluación finalizada.", "completadoTotal": True, "resultados": resultados}


def _alertar_riesgo(db: Session, participante: EvaluacionParticipante, resultados: list[dict]) -> None:
    criticos = [r for r in resultados if r["nivel"] in {"ALTO", "MUY_ALTO"}]
    if not criticos:
        return
    evaluacion = participante.evaluacion
    mensaje = (
        f"Se identificaron {len(criticos)} dimensión(es) en nivel alto o muy alto "
        "en una evaluación finalizada. Consulte los resultados en el panel institucional."
    )
    destinos = {evaluacion.evaluador_id}
    administradores = (
        db.query(Usuario)
        .join(Usuario.rol)
        .filter(Usuario.rol.has(codigo="SUPER_ADMINISTRADOR"), Usuario.estado == "ACTIVO")
        .all()
    )
    for admin in administradores:
        destinos.add(admin.id)
    for usuario_id in destinos:
        notificar(
            db,
            usuario_id=usuario_id,
            tipo="RIESGO_ALTO",
            titulo="Alerta de nivel de riesgo alto",
            mensaje=mensaje,
            evaluacion_id=evaluacion.id,
            commit=False,
        )


def _get_evaluacion(db: Session, evaluacion_id) -> Evaluacion:
    evaluacion = (
        db.query(Evaluacion)
        .options(joinedload(Evaluacion.participantes).joinedload(EvaluacionParticipante.trabajador))
        .filter(Evaluacion.id == evaluacion_id)
        .first()
    )
    if evaluacion is None:
        raise AppError(404, "Evaluación no encontrada.")
    return evaluacion


def _participante_trabajador(db: Session, evaluacion_id, actual: Usuario) -> EvaluacionParticipante:
    participante = (
        db.query(EvaluacionParticipante)
        .options(
            joinedload(EvaluacionParticipante.evaluacion),
            joinedload(EvaluacionParticipante.consentimiento),
            joinedload(EvaluacionParticipante.respuestas),
            joinedload(EvaluacionParticipante.instrumentos_asignados).joinedload(ParticipanteInstrumento.instrumento),
        )
        .filter(
            EvaluacionParticipante.evaluacion_id == evaluacion_id,
            EvaluacionParticipante.trabajador_id == actual.id,
        )
        .first()
    )
    if participante is None:
        raise AppError(403, "El acceso al cuestionario está restringido al trabajador asignado.")
    evaluacion = participante.evaluacion
    if evaluacion.estado == "FINALIZADA" and participante.estado != "COMPLETADA":
        raise AppError(400, "La evaluación ya no se encuentra vigente.")
    return participante


def _autorizar_consulta(actual: Usuario, evaluacion: Evaluacion) -> None:
    if actual.rol.codigo == "SUPER_ADMINISTRADOR":
        return
    if actual.rol.codigo in ROLES_EVALUADOR and evaluacion.evaluador_id == actual.id:
        return
    if actual.rol.codigo in {"TRABAJADOR", "PACIENTE"} and any(p.trabajador_id == actual.id for p in evaluacion.participantes):
        return
    raise AppError(403, "No tiene acceso a esta evaluación.")


def _serializar_evaluacion(evaluacion: Evaluacion, detalle: bool = False) -> dict:
    data = {
        "id": str(evaluacion.id),
        "nombre": evaluacion.nombre,
        "estado": evaluacion.estado,
        "organizacionId": str(evaluacion.organizacion_id),
        "evaluadorId": str(evaluacion.evaluador_id),
        "versionId": str(evaluacion.version_id),
        "fechaInicio": evaluacion.fecha_inicio.isoformat() if evaluacion.fecha_inicio else None,
        "fechaFin": evaluacion.fecha_fin.isoformat() if evaluacion.fecha_fin else None,
        "creadoEn": evaluacion.creado_en.isoformat(),
        "participantes": len(evaluacion.participantes),
    }
    if detalle:
        data["detalleParticipantes"] = [
            {
                "id": str(p.id),
                "trabajadorId": str(p.trabajador_id),
                "notificado": p.notificado,
                "estado": p.estado,
                "fechaNotificacion": p.fecha_notificacion.isoformat() if p.fecha_notificacion else None,
            }
            for p in evaluacion.participantes
        ]
        data["justificacionCierre"] = evaluacion.justificacion_cierre
    return data