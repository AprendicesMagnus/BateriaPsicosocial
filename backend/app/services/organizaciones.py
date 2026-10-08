from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.api.deps import asegurar_acceso_organizacion
from app.core.crypto import email_valido, hash_password, password_valida
from app.core.errors import AppError
from app.core.nit_utils import validar_nit_con_dv
from app.models.audit import Auditoria
from app.models.commercial import Compra
from app.models.evaluation import Evaluacion, EvaluacionParticipante, Notificacion
from app.models.organization import Area, Organizacion
from app.models.survey import SeguimientoRecomendacion
from app.models.user import Rol, Usuario
from app.services.auth import crear_y_enviar_codigo


def listar_organizaciones(db: Session, actual: Usuario) -> list[Organizacion]:
    query = db.query(Organizacion)
    if actual.rol.codigo != "SUPER_ADMINISTRADOR":
        query = query.filter(Organizacion.id == actual.organizacion_id)
    return query.order_by(Organizacion.nombre.asc()).all()


def existe_organizacion_nit(db: Session, nit: str) -> dict:
    nit_limpio = nit.strip()
    org = db.query(Organizacion).filter(Organizacion.nit == nit_limpio).first()
    if org:
        return {"existe": True, "organizacionId": str(org.id)}
    return {"existe": False, "organizacionId": None}


def autorregistrar_organizacion(db: Session, data, creador: Usuario | None = None) -> dict:
    """Registra de forma atómica una empresa y, si corresponde, su usuario responsable.

    Garantías de Seguridad y Diseño:
    1. Nunca se asigna un rol global (SUPER_ADMINISTRADOR) al usuario responsable: solo
       RESPONSABLE_SST (limitado) o EVALUADOR_SST (petición anónima), para evitar exposición
       de datos entre empresas.
    2. Si falla cualquier validación (NIT o Email duplicado, clave débil), se revierte
       toda la transacción sin dejar huérfanos.
    3. Se genera y envía el código de verificación de correo electrónico obligando
       a verificar la cuenta antes del login.
    """
    nit_limpio = data.nit.strip()
    validar_nit_con_dv(nit_limpio)
    if db.query(Organizacion).filter(Organizacion.nit == nit_limpio).first():
        raise AppError(409, "Ya existe una organización registrada con este NIT.")

    # Quién crea la empresa define si hace falta un usuario responsable:
    # - Psicologo (EVALUADOR_SST): él mismo es el responsable, no se crea otro usuario.
    # - Jefe / Administrador / Super Administrador: se crea un usuario limitado (RESPONSABLE_SST)
    #   que solo accede al módulo de Reportes.
    # - Petición anónima (sin sesión): se conserva el comportamiento anterior (EVALUADOR_SST).
    crea_psicologo = creador is not None and creador.rol.codigo == "EVALUADOR_SST"
    codigo_rol_responsable = "RESPONSABLE_SST" if creador is not None else "EVALUADOR_SST"

    usuario = None
    rol_responsable = None
    if not crea_psicologo:
        email_usuario = str(data.usuarioEmail).lower().strip() if data.usuarioEmail else ""
        if not data.usuarioNombre or not data.usuarioApellido or not email_usuario or not data.usuarioPassword:
            raise AppError(400, "Todos los datos del usuario responsable de la empresa son obligatorios.")

        if not email_valido(email_usuario):
            raise AppError(400, "El correo electrónico del usuario no es válido.")

        if not password_valida(data.usuarioPassword):
            raise AppError(
                400,
                "La contraseña debe tener mínimo 8 caracteres, e incluir mayúsculas, minúsculas y números.",
            )

        if db.query(Usuario).filter(Usuario.email == email_usuario).first():
            raise AppError(409, "Ya existe una cuenta registrada con este correo electrónico.")

        rol_responsable = db.query(Rol).filter(Rol.codigo == codigo_rol_responsable).first()
        if rol_responsable is None:
            raise AppError(500, f"El catálogo de roles ({codigo_rol_responsable}) no está inicializado.")

    try:
        org = Organizacion(
            nombre=data.nombre.strip(),
            nit=nit_limpio,
            sector=data.sector,
            municipio=data.municipio,
            email=str(data.email) if data.email else None,
            telefono=data.telefono,
            activa=True,
            creada_por_id=creador.id if creador is not None else None,
        )
        db.add(org)
        db.flush()

        if crea_psicologo:
            # El Psicologo es independiente y puede crear varias empresas. usuarios.organizacion_id
            # guarda su EMPRESA ACTIVA (sobre la que trabaja el Dashboard): la recién creada pasa a
            # ser la activa. Puede cambiarla cuando quiera con cambiar_empresa_activa().
            creador.organizacion_id = org.id
        else:
            usuario = Usuario(
                nombre=data.usuarioNombre.strip(),
                apellido=data.usuarioApellido.strip(),
                email=email_usuario,
                password_hash=hash_password(data.usuarioPassword),
                rol_id=rol_responsable.id,
                organizacion_id=org.id,
                email_verificado=False,
                estado="ACTIVO",
            )
            db.add(usuario)
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(org)
    if usuario is not None:
        db.refresh(usuario)
        crear_y_enviar_codigo(db, usuario, "VERIFICACION_EMAIL")

    return {
        "message": (
            "Empresa y cuenta creadas con éxito. Revisa tu correo para verificar tu cuenta."
            if usuario is not None and creador is None
            else "Empresa creada con éxito."
            if usuario is None
            else "Empresa creada. Se envió un código de verificación al correo del usuario responsable."
        ),
        "organizacionId": str(org.id),
        "usuarioId": str(usuario.id) if usuario is not None else None,
        "email": usuario.email if usuario is not None else None,
        "rol": rol_responsable.codigo if rol_responsable is not None else creador.rol.codigo,
        "usuarioCreado": usuario is not None,
    }


def listar_mis_organizaciones(db: Session, actual: Usuario) -> list[Organizacion]:
    """Empresas registradas por el usuario actual (sin importar a cuál esté vinculado)."""
    return (
        db.query(Organizacion)
        .filter(Organizacion.creada_por_id == actual.id)
        .order_by(Organizacion.creado_en.desc())
        .all()
    )


def crear_organizacion(db: Session, data) -> Organizacion:
    nit_limpio = data.nit.strip()
    validar_nit_con_dv(nit_limpio)
    if db.query(Organizacion).filter(Organizacion.nit == nit_limpio).first():
        raise AppError(409, "Ya existe una organización con ese NIT.")
    org = Organizacion(
        nombre=data.nombre.strip(),
        nit=nit_limpio,
        sector=data.sector,
        municipio=data.municipio,
        telefono=data.telefono,
        email=str(data.email) if data.email else None,
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


def actualizar_organizacion(db: Session, org_id, data) -> Organizacion:
    org = db.query(Organizacion).filter(Organizacion.id == org_id).first()
    if org is None:
        raise AppError(404, "Organización no encontrada.")
    if data.nit is not None:
        nit_limpio = data.nit.strip()
        validar_nit_con_dv(nit_limpio)
    for campo, valor in {
        "nombre": data.nombre,
        "nit": data.nit,
        "sector": data.sector,
        "municipio": data.municipio,
        "telefono": data.telefono,
        "activa": data.activa,
    }.items():
        if valor is not None:
            setattr(org, campo, valor.strip() if isinstance(valor, str) else valor)
    if data.email is not None:
        org.email = str(data.email)
    db.commit()
    db.refresh(org)
    return org


def listar_areas(db: Session, organizacion_id, actual: Usuario) -> list[Area]:
    asegurar_acceso_organizacion(actual, organizacion_id)
    return db.query(Area).filter(Area.organizacion_id == organizacion_id).order_by(Area.nombre.asc()).all()


def crear_area(db: Session, data, actual: Usuario) -> Area:
    asegurar_acceso_organizacion(actual, data.organizacionId)
    if db.query(Organizacion).filter(Organizacion.id == data.organizacionId).first() is None:
        raise AppError(404, "Organización no encontrada.")
    existe = (
        db.query(Area)
        .filter(Area.organizacion_id == data.organizacionId, Area.nombre == data.nombre.strip())
        .first()
    )
    if existe:
        raise AppError(409, "Ya existe un área con ese nombre en la organización.")
    area = Area(organizacion_id=data.organizacionId, nombre=data.nombre.strip(), activa=True)
    db.add(area)
    db.commit()
    db.refresh(area)
    return area


def actualizar_area(db: Session, area_id, data, actual: Usuario) -> Area:
    area = db.query(Area).filter(Area.id == area_id).first()
    if area is None:
        raise AppError(404, "Área no encontrada.")
    asegurar_acceso_organizacion(actual, area.organizacion_id)
    if data.nombre is not None:
        area.nombre = data.nombre.strip()
    if data.activa is not None:
        area.activa = data.activa
    db.commit()
    db.refresh(area)
    return area


def eliminar_area(db: Session, area_id, actual: Usuario) -> dict:
    area = db.query(Area).filter(Area.id == area_id).first()
    if area is None:
        raise AppError(404, "Área no encontrada.")
    asegurar_acceso_organizacion(actual, area.organizacion_id)
    if db.query(Usuario).filter(Usuario.area_id == area.id).first():
        raise AppError(400, "No se puede eliminar un área que tiene trabajadores asociados.")
    participantes = (
        db.query(EvaluacionParticipante)
        .join(Usuario, Usuario.id == EvaluacionParticipante.trabajador_id)
        .filter(Usuario.area_id == area.id)
        .first()
    )
    if participantes:
        raise AppError(400, "No se puede eliminar un área que tiene evaluaciones asociadas.")
    db.delete(area)
    db.commit()
    return {"message": "Área eliminada."}


# --- Edición y eliminación de "Mis Empresas" -------------------------------------------------


def _obtener_organizacion_propia(db: Session, org_id, actual: Usuario) -> Organizacion:
    """La empresa debe existir y ser del usuario (o ser Super Administrador)."""
    org = db.query(Organizacion).filter(Organizacion.id == org_id).first()
    if org is None:
        raise AppError(404, "Empresa no encontrada.")
    if org.creada_por_id != actual.id and actual.rol.codigo != "SUPER_ADMINISTRADOR":
        raise AppError(403, "Solo puedes gestionar las empresas que tú creaste.")
    return org


def actualizar_mi_organizacion(db: Session, org_id, data, actual: Usuario) -> Organizacion:
    org = _obtener_organizacion_propia(db, org_id, actual)
    cambios = data.model_dump(exclude_unset=True, exclude_none=True)
    if not cambios:
        raise AppError(400, "No enviaste ningún cambio.")
    # Razón social y NIT no se pueden modificar desde aquí.
    for campo in ("sector", "municipio"):
        if campo in cambios:
            setattr(org, campo, cambios[campo].strip())
    if "email" in cambios:
        org.email = str(cambios["email"]).lower().strip()
    if "telefono" in cambios:
        org.telefono = cambios["telefono"].strip()
    db.commit()
    db.refresh(org)
    return org


def eliminar_mi_organizacion(db: Session, org_id, actual: Usuario) -> dict:
    """Elimina una empresa que aún no tiene actividad.

    Se bloquea si ya tiene evaluaciones, compras o seguimiento de recomendaciones, para no
    perder información. Al eliminarla:
    - los usuarios RESPONSABLE_SST creados para esta empresa se eliminan (quedarían sin acceso);
    - cualquier otro usuario vinculado (p. ej. el Psicologo que la creó) queda sin empresa;
    - se eliminan sus áreas.
    """
    org = _obtener_organizacion_propia(db, org_id, actual)

    if db.query(Evaluacion).filter(Evaluacion.organizacion_id == org.id).first():
        raise AppError(409, "No se puede eliminar: la empresa ya tiene evaluaciones registradas.")
    if db.query(Compra).filter(Compra.organizacion_id == org.id).first():
        raise AppError(409, "No se puede eliminar: la empresa ya tiene compras registradas.")
    if db.query(SeguimientoRecomendacion).filter(SeguimientoRecomendacion.organizacion_id == org.id).first():
        raise AppError(409, "No se puede eliminar: la empresa ya tiene seguimiento de recomendaciones.")

    vinculados = db.query(Usuario).options(joinedload(Usuario.rol)).filter(Usuario.organizacion_id == org.id).all()
    responsables = [u for u in vinculados if u.rol.codigo == "RESPONSABLE_SST"]
    ids_responsables = [u.id for u in responsables]
    if ids_responsables and db.query(Compra).filter(Compra.usuario_id.in_(ids_responsables)).first():
        raise AppError(409, "No se puede eliminar: un usuario de la empresa tiene compras registradas.")

    try:
        for usuario in vinculados:
            if usuario.rol.codigo != "RESPONSABLE_SST":
                usuario.organizacion_id = None
        if ids_responsables:
            db.query(Notificacion).filter(Notificacion.usuario_id.in_(ids_responsables)).delete(
                synchronize_session=False
            )
            db.query(Auditoria).filter(Auditoria.usuario_id.in_(ids_responsables)).update(
                {Auditoria.usuario_id: None}, synchronize_session=False
            )
            for usuario in responsables:
                db.delete(usuario)
        db.flush()
        db.query(Area).filter(Area.organizacion_id == org.id).delete(synchronize_session=False)
        db.delete(org)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise AppError(409, "No se puede eliminar: la empresa tiene información asociada.")

    return {"message": "Empresa eliminada correctamente."}


def cambiar_empresa_activa(db: Session, actual: Usuario, org_id) -> Usuario:
    """El Psicologo elige con cuál de las empresas que creó trabaja (Dashboard, reportes, enlaces...)."""
    if actual.rol.codigo != "EVALUADOR_SST":
        raise AppError(403, "Solo el Psicologo puede cambiar de empresa activa.")
    org = (
        db.query(Organizacion)
        .filter(Organizacion.id == org_id, Organizacion.creada_por_id == actual.id)
        .first()
    )
    if org is None:
        raise AppError(404, "No se encontró esa empresa entre las que creaste.")
    actual.organizacion_id = org.id
    db.commit()
    db.refresh(actual)
    return actual
