from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.audit import Auditoria
from app.models.commercial import Compra
from app.models.evaluation import Evaluacion, EvaluacionParticipante
from app.models.organization import Organizacion
from app.models.user import Usuario

# accion de auditoría -> pestaña del filtro del panel
TIPO_POR_ACCION = {
    "INFORME_INDIVIDUAL_GENERADO": "Resultados",
    "INFORME_AGRUPADO_GENERADO": "Resultados",
    "CREAR_USUARIO": "Usuarios",
    "ACTUALIZAR_USUARIO": "Usuarios",
    "DESACTIVAR_USUARIO": "Usuarios",
    "CAMBIAR_ROL_USUARIO": "Usuarios",
    "CREAR_ENLACE_PACIENTES": "Enlaces",
    "ELIMINAR_ENLACE_PACIENTES": "Enlaces",
}


def _nombre(u: Usuario | None) -> str:
    return f"{u.nombre} {u.apellido}".strip() if u else "Sistema"


def obtener_panel(db: Session) -> dict:
    orgs = {o.id: o for o in db.query(Organizacion).all()}

    # Último acceso y tipo de registro, sacados de los LOGIN de auditoría
    ultimos = dict(
        db.query(Auditoria.usuario_id, func.max(Auditoria.registrado_en))
        .filter(Auditoria.accion.in_(["LOGIN", "LOGIN_GOOGLE"]))
        .group_by(Auditoria.usuario_id)
        .all()
    )
    con_google = {
        uid
        for (uid,) in db.query(Auditoria.usuario_id)
        .filter(Auditoria.accion == "LOGIN_GOOGLE")
        .distinct()
    }

    usuarios_db = (
        db.query(Usuario)
        .options(joinedload(Usuario.rol))
        .filter(Usuario.es_invitado.is_(False))
        .order_by(Usuario.fecha_registro.desc())
        .all()
    )
    usuarios = [
        {
            "id": str(u.id),
            "nombre": _nombre(u),
            "correo": u.email,
            "rol": u.rol.codigo,
            "empresa": orgs[u.organizacion_id].nombre if u.organizacion_id in orgs else "—",
            "registro": "Google" if u.id in con_google else "Correo",
            "estado": u.estado,
            "emailVerificado": u.email_verificado,
            "ultimoAcceso": ultimos[u.id].isoformat() if u.id in ultimos else None,
        }
        for u in usuarios_db
    ]

    # Encuestas completadas por empresa
    completadas = dict(
        db.query(Evaluacion.organizacion_id, func.count(EvaluacionParticipante.id))
        .join(EvaluacionParticipante, EvaluacionParticipante.evaluacion_id == Evaluacion.id)
        .filter(EvaluacionParticipante.estado == "COMPLETADA")
        .group_by(Evaluacion.organizacion_id)
        .all()
    )
    # Evaluaciones compradas (pagadas) por empresa
    compradas = dict(
        db.query(Compra.organizacion_id, func.sum(Compra.cantidad))
        .filter(Compra.estado == "PAGADA")
        .group_by(Compra.organizacion_id)
        .all()
    )
    responsables = {
        u.organizacion_id: _nombre(u)
        for u in usuarios_db
        if u.rol.codigo == "RESPONSABLE_SST" and u.organizacion_id
    }
    empresas = [
        {
            "id": str(o.id),
            "nit": o.nit,
            "nombre": o.nombre,
            "responsable": responsables.get(o.id, "—"),
            "encuestas": completadas.get(o.id, 0),
            "usadas": completadas.get(o.id, 0),
            "compradas": int(compradas.get(o.id) or 0),
        }
        for o in orgs.values()
    ]

    # Compras con su último pago
    compras_db = (
        db.query(Compra)
        .options(joinedload(Compra.pagos))
        .order_by(Compra.creado_en.desc())
        .limit(50)
        .all()
    )
    compras = []
    for c in compras_db:
        pago = max(c.pagos, key=lambda p: p.procesado_en, default=None)
        medio = "—"
        if pago:
            medio = pago.metodo + (f" •••• {pago.ultimos_digitos}" if pago.ultimos_digitos else "")
        compras.append({
            "id": str(c.id),
            "fecha": c.creado_en.isoformat(),
            "empresa": orgs[c.organizacion_id].nombre if c.organizacion_id in orgs else "—",
            "cantidad": c.cantidad,
            "medio": medio,
            "valor": c.total,
            "estado": c.estado,
        })

    total_compradas = sum(e["compradas"] for e in empresas)
    total_usadas = sum(e["usadas"] for e in empresas)

    # Auditoría
    nombres = {u.id: _nombre(u) for u in usuarios_db}
    auditoria = [
        {
            "id": str(a.id),
            "usuario": nombres.get(a.usuario_id, "Sistema"),
            "accion": a.accion,
            "detalle": a.nota or a.entidad or "",
            "tipo": TIPO_POR_ACCION.get(a.accion, "Usuarios"),
            "fecha": a.registrado_en.isoformat(),
        }
        for a in db.query(Auditoria).order_by(Auditoria.registrado_en.desc()).limit(100)
    ]

    return {
        "usuarios": usuarios,
        "empresas": empresas,
        "compras": compras,
        "saldo": {"compradas": total_compradas, "usadas": total_usadas},
        "auditoria": auditoria,
    }
