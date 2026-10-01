"""Enlaces públicos para que los pacientes respondan la batería sin crear cuenta.

Flujo:
1. El psicólogo (EVALUADOR_SST) crea un enlace: se crea una evaluación de su organización
   con un token aleatorio (Evaluacion.enlace_token).
2. El paciente abre /responder/<token>, acepta el consentimiento y pulsa "Comenzar".
3. Se crea un usuario invitado (TRABAJADOR, es_invitado=True) y su participación en la evaluación,
   y se le devuelve un token de sesión. Desde ahí usa el flujo normal de la batería
   (Ficha de datos -> Estrés -> Extralaboral -> Intralaboral) con los endpoints de /evaluaciones.
4. Al guardar la Ficha, el nombre del invitado se toma del "nombre completo" (guardar_ficha_datos),
   y así el psicólogo sabe quién respondió en "Encuestas realizadas" (Reportes).
5. Cada enlace es para un solo paciente: cuando alguien empieza ya no se puede reutilizar, y al
   terminar la batería la evaluación pasa a FINALIZADA (finalizar_cuestionario) y el enlace se cierra.
"""
import secrets
import uuid

from sqlalchemy.orm import Session, joinedload

from app.core.crypto import hash_password, utcnow
from app.core.errors import AppError
from app.core.security import crear_token
from app.models.evaluation import Consentimiento, Evaluacion, EvaluacionParticipante, ParticipanteInstrumento
from app.db.seed import ROLES
from app.models.user import Rol, Usuario
from app.services.auth import usuario_publico
from app.services.cuestionarios import version_vigente
from app.services.evaluaciones import TEXTO_CONSENTIMIENTO, _inicializar_instrumentos_evaluacion

# La sesión del paciente dura 7 días para que pueda retomar la batería en el mismo navegador
MINUTOS_SESION_INVITADO = 7 * 24 * 60


def _serializar_enlace(evaluacion: Evaluacion) -> dict:
    # Cada enlace es de un solo paciente. Su nombre sale de la Ficha de datos: mientras no la
    # guarde (participante en PENDIENTE) todavía no se sabe quién es
    participante = evaluacion.participantes[0] if evaluacion.participantes else None
    paciente = None
    if participante is not None:
        trabajador = participante.trabajador
        paciente = {
            "nombre": (
                f"{trabajador.nombre} {trabajador.apellido}".strip()
                if participante.estado != "PENDIENTE"
                else None
            ),
            "estado": participante.estado,  # PENDIENTE / EN_PROGRESO / COMPLETADA
        }
    return {
        "evaluacionId": str(evaluacion.id),
        "nombre": evaluacion.nombre,
        "estado": evaluacion.estado,
        "token": evaluacion.enlace_token,
        "creadoEn": evaluacion.creado_en.isoformat(),
        "participantes": len(evaluacion.participantes),
        "completados": sum(1 for p in evaluacion.participantes if p.estado == "COMPLETADA"),
        # null si nadie ha abierto el enlace todavía
        "paciente": paciente,
    }


def crear_enlace(db: Session, nombre: str, actual: Usuario) -> dict:
    if not actual.organizacion_id:
        raise AppError(400, "Tu usuario no tiene una organización asociada; no se puede crear el enlace.")
    version = version_vigente(db)
    evaluacion = Evaluacion(
        organizacion_id=actual.organizacion_id,
        evaluador_id=actual.id,
        version_id=version.id,
        nombre=nombre.strip(),
        # Queda abierta de una vez para que los pacientes puedan responder
        estado="EN_CURSO",
        fecha_inicio=utcnow(),
        enlace_token=secrets.token_urlsafe(24),
    )
    db.add(evaluacion)
    db.flush()
    # Crea los instrumentos de la evaluación (Ficha, Estrés, Extralaboral); aún sin participantes
    _inicializar_instrumentos_evaluacion(db, evaluacion, [])
    db.commit()
    db.refresh(evaluacion)
    return _serializar_enlace(evaluacion)


def listar_enlaces(db: Session, actual: Usuario) -> list[dict]:
    query = (
        db.query(Evaluacion)
        .options(joinedload(Evaluacion.participantes).joinedload(EvaluacionParticipante.trabajador))
        .filter(Evaluacion.enlace_token.isnot(None), Evaluacion.enlace_oculto_en.is_(None))
    )
    if actual.rol.codigo != "SUPER_ADMINISTRADOR":
        query = query.filter(Evaluacion.evaluador_id == actual.id)
    return [_serializar_enlace(e) for e in query.order_by(Evaluacion.creado_en.desc()).all()]


def _quitar_enlace(db: Session, evaluacion: Evaluacion) -> None:
    """Quita el enlace de la lista sin tocar "Encuestas realizadas".

    - Nadie lo abrió: se borra la evaluación vacía (y sus instrumentos); no hay datos que perder.
    - Ya lo usó un paciente: solo se oculta. La evaluación, sus respuestas y resultados se conservan,
      y si el paciente no ha terminado puede seguir respondiendo con su sesión.
    """
    if evaluacion.participantes:
        evaluacion.enlace_oculto_en = utcnow()
    else:
        db.delete(evaluacion)


def eliminar_enlace(db: Session, evaluacion_id, actual: Usuario) -> dict:
    evaluacion = (
        db.query(Evaluacion)
        .options(joinedload(Evaluacion.participantes))
        .filter(
            Evaluacion.id == evaluacion_id,
            Evaluacion.enlace_token.isnot(None),
            Evaluacion.enlace_oculto_en.is_(None),
        )
        .first()
    )
    if evaluacion is None:
        raise AppError(404, "El enlace no existe o ya fue eliminado.")
    if actual.rol.codigo != "SUPER_ADMINISTRADOR" and evaluacion.evaluador_id != actual.id:
        raise AppError(403, "Solo el psicólogo que creó el enlace puede eliminarlo.")
    _quitar_enlace(db, evaluacion)
    db.commit()
    return {"message": "Enlace eliminado."}


def limpiar_enlaces(db: Session) -> int:
    """Limpieza automática (cada 4 horas, ver app/main.py): vacía la lista de enlaces de todos."""
    evaluaciones = (
        db.query(Evaluacion)
        .options(joinedload(Evaluacion.participantes))
        .filter(Evaluacion.enlace_token.isnot(None), Evaluacion.enlace_oculto_en.is_(None))
        .all()
    )
    for evaluacion in evaluaciones:
        _quitar_enlace(db, evaluacion)
    db.commit()
    return len(evaluaciones)


def _rol_paciente(db: Session) -> Rol:
    """Rol de los invitados. Lo crea el seed; si la BD aún no se ha vuelto a sembrar, se crea aquí."""
    rol = db.query(Rol).filter(Rol.codigo == "PACIENTE").first()
    if rol is None:
        datos = ROLES["PACIENTE"]
        rol = Rol(codigo="PACIENTE", nombre=datos["nombre"], descripcion=datos["descripcion"], es_sistema=True, activo=True)
        db.add(rol)
        db.flush()
    return rol


def _evaluacion_por_token(db: Session, token: str) -> Evaluacion:
    evaluacion = (
        db.query(Evaluacion)
        .options(
            joinedload(Evaluacion.organizacion),
            joinedload(Evaluacion.evaluador),
            joinedload(Evaluacion.participantes),
        )
        .filter(Evaluacion.enlace_token == token)
        .first()
    )
    if evaluacion is None:
        raise AppError(404, "El enlace no existe o fue eliminado.")
    return evaluacion


def info_publica(db: Session, token: str) -> dict:
    """Lo que ve el paciente antes de empezar (sin sesión)."""
    evaluacion = _evaluacion_por_token(db, token)
    evaluador = evaluacion.evaluador
    return {
        "nombre": evaluacion.nombre,
        "organizacionNombre": evaluacion.organizacion.nombre if evaluacion.organizacion else None,
        "evaluadorNombre": f"{evaluador.nombre} {evaluador.apellido}".strip() if evaluador else None,
        "activo": evaluacion.estado != "FINALIZADA",
        # Ya hay un paciente respondiendo con este enlace (solo lo puede continuar él)
        "enUso": len(evaluacion.participantes) > 0,
    }


def iniciar_como_invitado(db: Session, token: str, ip: str | None) -> dict:
    """Crea el paciente invitado, su participación y su consentimiento, y le abre sesión."""
    evaluacion = _evaluacion_por_token(db, token)
    if evaluacion.estado == "FINALIZADA":
        raise AppError(400, "Este enlace ya fue cerrado.")
    # Un enlace = un paciente: si otra persona ya empezó a responder, no se puede reutilizar
    if evaluacion.participantes:
        raise AppError(400, "Este enlace ya está siendo usado por otro paciente. Pide un enlace nuevo a tu psicólogo.")

    rol = _rol_paciente(db)

    # Nombre provisional: se reemplaza con el nombre completo de la Ficha de datos
    invitado = Usuario(
        nombre="Paciente",
        apellido="(sin ficha)",
        email=f"invitado-{uuid.uuid4().hex}@enlace.invitado",
        # Contraseña aleatoria que nadie conoce; además el login rechaza a los invitados
        password_hash=hash_password(secrets.token_urlsafe(32)),
        rol_id=rol.id,
        estado="ACTIVO",
        email_verificado=True,
        organizacion_id=evaluacion.organizacion_id,
        es_invitado=True,
    )
    db.add(invitado)
    db.flush()

    ahora = utcnow()
    participante = EvaluacionParticipante(
        evaluacion_id=evaluacion.id,
        trabajador_id=invitado.id,
        notificado=True,
        fecha_notificacion=ahora,
    )
    db.add(participante)
    db.flush()

    # Mismos instrumentos que tiene la evaluación (el intralaboral A/B lo asigna la Ficha)
    for instrumento in evaluacion.instrumentos:
        db.add(ParticipanteInstrumento(participante_id=participante.id, instrumento_id=instrumento.id, estado="PENDIENTE"))

    # El paciente aceptó el consentimiento en la página del enlace antes de pulsar "Comenzar"
    db.add(
        Consentimiento(
            participante_id=participante.id,
            trabajador_id=invitado.id,
            aceptado=True,
            texto_version=TEXTO_CONSENTIMIENTO,
            ip_origen=ip,
        )
    )
    db.commit()
    db.refresh(invitado)

    token_sesion = crear_token(
        {"sub": str(invitado.id), "rol": rol.codigo, "email": invitado.email},
        MINUTOS_SESION_INVITADO,
    )
    return {"token": token_sesion, "usuario": usuario_publico(invitado), "evaluacionId": str(evaluacion.id)}
