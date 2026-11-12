from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.audit import Auditoria
from app.models.commercial import Compra
from app.models.product_order import PedidoProducto
from app.models.evaluation import Evaluacion, EvaluacionParticipante
from app.models.organization import Organizacion
from app.models.user import Usuario

# accion de auditoría -> pestaña del filtro del panel
TIPO_POR_ACCION = {
    "INFORME_INDIVIDUAL_GENERADO": "Resultados",
    "INFORME_AGRUPADO_GENERADO": "Resultados",
    "INFORME_DESCARGADO": "Resultados",
    "INFORMES_EXCEL_DESCARGADOS": "Resultados",
    "LOGIN": "Accesos",
    "LOGIN_GOOGLE": "Accesos",
    "LOGIN_2FA": "Accesos",
    "CREAR_EVALUACION": "Evaluaciones",
    "INICIAR_EVALUACION": "Evaluaciones",
    "FINALIZAR_EVALUACION": "Evaluaciones",
    "EDITAR_EMPRESA": "Empresas",
    "EDITAR_RESPONSABLE_EMPRESA": "Empresas",
    "ELIMINAR_EMPRESA": "Empresas",
    "CAMBIAR_EMPRESA_ACTIVA": "Empresas",
    "CREAR_PLAN": "Planes",
    "EDITAR_PLAN": "Planes",
    "ELIMINAR_PLAN": "Planes",
    "CREAR_USUARIO": "Usuarios",
    "ACTUALIZAR_USUARIO": "Usuarios",
    "DESACTIVAR_USUARIO": "Usuarios",
    "CAMBIAR_ROL_USUARIO": "Usuarios",
    "CREAR_ENLACE_PACIENTES": "Enlaces",
    "ELIMINAR_ENLACE_PACIENTES": "Enlaces",
    "EXPORTAR_PANEL": "Usuarios",
    "POLITICA_ACEPTADA": "Usuarios",
    "DATOS_DESCARGADOS": "Usuarios",
    "ELIMINACION_SOLICITADA": "Usuarios",
}


def _nombre(u: Usuario | None) -> str:
    return f"{u.nombre} {u.apellido}".strip() if u else "Sistema"


def obtener_panel(db: Session) -> dict:
    orgs = {o.id: o for o in db.query(Organizacion).all()}

    # Último acceso y tipo de registro, sacados de los LOGIN de auditoría
    ultimos = dict(
        db.query(Auditoria.usuario_id, func.max(Auditoria.registrado_en))
        .filter(Auditoria.accion.in_(["LOGIN", "LOGIN_GOOGLE", "LOGIN_2FA"]))
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
            "nombrePila": u.nombre,
            "apellido": u.apellido,
            "rol": u.rol.codigo,
            "empresa": (
                orgs[u.organizacion_id].nombre
                if u.organizacion_id in orgs
                else "MAGNUS | SIG" if u.rol.codigo == "SUPER_ADMINISTRADOR" else "—"
            ),
            "registro": "Google" if u.id in con_google else "Correo",
            "estado": u.estado,
            "emailVerificado": u.email_verificado,
            "ultimoAcceso": ultimos[u.id].isoformat() if u.id in ultimos else None,
            "numeroResolucion": u.numero_resolucion,
            "resolucionVerificada": u.resolucion_verificada,
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


def obtener_historial_compras_tienda(db: Session) -> list[dict]:
    """Historial unificado de compras de planes/baterías y productos."""
    usuarios = {
        u.id: u
        for u in db.query(Usuario).all()
    }
    orgs = {o.id: o for o in db.query(Organizacion).all()}

    historial = []

    compras = (
        db.query(Compra)
        .order_by(Compra.creado_en.desc())
        .all()
    )
    for compra in compras:
        usuario = usuarios.get(compra.usuario_id)
        historial.append({
            "id": str(compra.id),
            "tipo": "Plan de baterías",
            "detalle": compra.bateria_nombre,
            "fecha": compra.creado_en.isoformat(),
            "nombre": _nombre(usuario),
            "empresa": orgs[compra.organizacion_id].nombre if compra.organizacion_id in orgs else "—",
            "total": compra.total,
            "estado": compra.estado,
        })

    pedidos = (
        db.query(PedidoProducto)
        .options(joinedload(PedidoProducto.items))
        .order_by(PedidoProducto.creado_en.desc())
        .all()
    )
    for pedido in pedidos:
        usuario = usuarios.get(pedido.usuario_id)
        detalle = ", ".join(
            f"{item.nombre_producto} x{item.cantidad}"
            for item in pedido.items
        ) or "Productos"
        historial.append({
            "id": str(pedido.id),
            "tipo": "Producto",
            "detalle": detalle,
            "fecha": pedido.creado_en.isoformat(),
            "nombre": _nombre(usuario),
            "empresa": orgs[usuario.organizacion_id].nombre
            if usuario and usuario.organizacion_id in orgs else "—",
            "total": pedido.total,
            "estado": pedido.estado,
        })

    historial.sort(key=lambda x: x["fecha"], reverse=True)
    return historial


MESES_ES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def obtener_evolucion_mensual(db: Session, meses: int = 12) -> dict:
    ahora = datetime.now(timezone.utc)
    lista_meses = []
    y, m = ahora.year, ahora.month
    for _ in range(meses):
        lista_meses.append((y, m))
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    lista_meses.reverse()

    y_ini, m_ini = lista_meses[0]
    fecha_inicio = datetime(y_ini, m_ini, 1, tzinfo=timezone.utc)

    # a) usuariosNuevos: Usuario.fecha_registro, solo Usuario.es_invitado == False
    col_mes_usr = func.date_trunc("month", Usuario.fecha_registro).label("mes")
    res_usuarios = (
        db.query(col_mes_usr, func.count(Usuario.id))
        .filter(
            Usuario.es_invitado.is_(False),
            Usuario.fecha_registro >= fecha_inicio,
        )
        .group_by(col_mes_usr)
        .all()
    )

    # b) evaluacionesCreadas: Evaluacion.creado_en
    col_mes_eval = func.date_trunc("month", Evaluacion.creado_en).label("mes")
    res_evaluaciones = (
        db.query(col_mes_eval, func.count(Evaluacion.id))
        .filter(Evaluacion.creado_en >= fecha_inicio)
        .group_by(col_mes_eval)
        .all()
    )

    # c) encuestasCompletadas: EvaluacionParticipante con estado == "COMPLETADA", agrupadas por fecha_fin
    col_mes_part = func.date_trunc("month", EvaluacionParticipante.fecha_fin).label("mes")
    res_encuestas = (
        db.query(col_mes_part, func.count(EvaluacionParticipante.id))
        .filter(
            EvaluacionParticipante.estado == "COMPLETADA",
            EvaluacionParticipante.fecha_fin.isnot(None),
            EvaluacionParticipante.fecha_fin >= fecha_inicio,
        )
        .group_by(col_mes_part)
        .all()
    )

    # d) comprasPagadas y valorComprado: Compra con estado == "PAGADA", por Compra.creado_en
    col_mes_compra = func.date_trunc("month", Compra.creado_en).label("mes")
    res_compras = (
        db.query(
            col_mes_compra,
            func.coalesce(func.sum(Compra.cantidad), 0),
            func.coalesce(func.sum(Compra.total), 0),
        )
        .filter(
            Compra.estado == "PAGADA",
            Compra.creado_en >= fecha_inicio,
        )
        .group_by(col_mes_compra)
        .all()
    )

    def _clave_mes(dt) -> str:
        if dt is None:
            return ""
        return f"{dt.year:04d}-{dt.month:02d}"

    usuarios_map = {_clave_mes(r[0]): int(r[1]) for r in res_usuarios if r[0]}
    evals_map = {_clave_mes(r[0]): int(r[1]) for r in res_evaluaciones if r[0]}
    encuestas_map = {_clave_mes(r[0]): int(r[1]) for r in res_encuestas if r[0]}
    compras_map = {
        _clave_mes(r[0]): (int(r[1]), int(r[2]))
        for r in res_compras if r[0]
    }

    puntos = []
    for y, m in lista_meses:
        clave = f"{y:04d}-{m:02d}"
        etiqueta = f"{MESES_ES[m - 1]} {y}"
        c_pagadas, v_comprado = compras_map.get(clave, (0, 0))
        puntos.append({
            "mes": clave,
            "etiqueta": etiqueta,
            "usuariosNuevos": usuarios_map.get(clave, 0),
            "evaluacionesCreadas": evals_map.get(clave, 0),
            "encuestasCompletadas": encuestas_map.get(clave, 0),
            "comprasPagadas": c_pagadas,
            "valorComprado": v_comprado,
        })

    return {"meses": puntos}


def obtener_seguimiento_baterias(db: Session) -> dict:
    """Resumen operativo de compras, consumo y actividad por empresa y usuario.

    Las baterías se acreditan solo con compras PAGADAS y se consumen cuando
    el paciente guarda su primera respuesta (Evaluacion.bateria_consumida_en).
    """
    organizaciones = db.query(Organizacion).order_by(Organizacion.nombre.asc()).all()
    usuarios_todos = (
        db.query(Usuario)
        .options(joinedload(Usuario.rol))
        .filter(Usuario.es_invitado.is_(False))
        .order_by(Usuario.nombre.asc(), Usuario.apellido.asc())
        .all()
    )
    usuarios_db = [u for u in usuarios_todos if u.estado != "INACTIVO"]
    nombres_usuario = {u.id: _nombre(u) for u in usuarios_todos}
    nombres_org = {o.id: o.nombre for o in organizaciones}
    organizaciones_por_creador = {}
    for org in organizaciones:
        if org.creada_por_id:
            organizaciones_por_creador.setdefault(org.creada_por_id, []).append(org.id)

    compras_pagadas = (
        db.query(Compra)
        .options(joinedload(Compra.pagos))
        .filter(Compra.estado == "PAGADA")
        .order_by(Compra.creado_en.desc())
        .all()
    )
    compras_por_org = {}
    compras_por_usuario_org = {}
    ultima_compra_org = {}
    for compra in compras_pagadas:
        if compra.organizacion_id:
            compras_por_org[compra.organizacion_id] = compras_por_org.get(compra.organizacion_id, 0) + int(compra.cantidad or 0)
            clave = (compra.organizacion_id, compra.usuario_id)
            compras_por_usuario_org[clave] = compras_por_usuario_org.get(clave, 0) + int(compra.cantidad or 0)
            pago_aprobado = max(
                (p for p in compra.pagos if p.estado == "APROBADO"),
                key=lambda p: p.procesado_en,
                default=None,
            )
            fecha_compra = pago_aprobado.procesado_en if pago_aprobado else compra.creado_en
            if compra.organizacion_id not in ultima_compra_org or fecha_compra > ultima_compra_org[compra.organizacion_id]:
                ultima_compra_org[compra.organizacion_id] = fecha_compra

    consumos = (
        db.query(Evaluacion.organizacion_id, Evaluacion.evaluador_id, func.count(Evaluacion.id))
        .filter(
            Evaluacion.bateria_controlada.is_(True),
            Evaluacion.bateria_consumida_en.isnot(None),
        )
        .group_by(Evaluacion.organizacion_id, Evaluacion.evaluador_id)
        .all()
    )
    consumidas_por_org = {}
    consumidas_por_usuario_org = {}
    for org_id, usuario_id, cantidad in consumos:
        consumidas_por_org[org_id] = consumidas_por_org.get(org_id, 0) + int(cantidad or 0)
        consumidas_por_usuario_org[(org_id, usuario_id)] = int(cantidad or 0)

    actividad_org = dict(
        db.query(Evaluacion.organizacion_id, func.max(Evaluacion.bateria_consumida_en))
        .filter(Evaluacion.bateria_consumida_en.isnot(None))
        .group_by(Evaluacion.organizacion_id)
        .all()
    )
    actividad_usuario_org = {
        (org_id, usuario_id): fecha
        for org_id, usuario_id, fecha in (
            db.query(Evaluacion.organizacion_id, Evaluacion.evaluador_id, func.max(Evaluacion.bateria_consumida_en))
            .filter(Evaluacion.bateria_consumida_en.isnot(None))
            .group_by(Evaluacion.organizacion_id, Evaluacion.evaluador_id)
            .all()
        )
    }

    empresas = []
    for org in organizaciones:
        compradas = int(compras_por_org.get(org.id, 0))
        consumidas = int(consumidas_por_org.get(org.id, 0))
        disponibles = max(0, compradas - consumidas)
        miembros = [
            u for u in usuarios_db
            if u.organizacion_id == org.id or org.creada_por_id == u.id
        ]
        if compradas == 0:
            estado = "SIN_COMPRA"
        elif disponibles == 0:
            estado = "AGOTADAS"
        elif disponibles <= 5:
            estado = "POR_AGOTARSE"
        else:
            estado = "DISPONIBLES"
        empresas.append({
            "id": str(org.id),
            "nombre": org.nombre,
            "nit": org.nit,
            "responsable": next((_nombre(u) for u in miembros if u.rol.codigo == "RESPONSABLE_SST"), "—"),
            "usuarios": len(miembros),
            "compras": sum(1 for c in compras_pagadas if c.organizacion_id == org.id),
            "compradas": compradas,
            "consumidas": consumidas,
            "disponibles": disponibles,
            "estado": estado,
            "ultimaCompra": ultima_compra_org[org.id].isoformat() if org.id in ultima_compra_org else None,
            "ultimaActividad": actividad_org[org.id].isoformat() if actividad_org.get(org.id) else None,
        })

    usuarios = []
    for u in usuarios_db:
        if u.rol.codigo not in {"EVALUADOR_SST", "RESPONSABLE_SST", "ADMINISTRADOR", "JEFE"}:
            continue
        # Psicólogos, Jefes y Administradores pueden administrar empresas que crearon;
        # se muestra una fila por empresa para no mezclar sus saldos entre organizaciones.
        org_ids = set(organizaciones_por_creador.get(u.id, []))
        if u.organizacion_id:
            org_ids.add(u.organizacion_id)
        if not org_ids:
            org_ids = {None}
        for org_id in sorted(org_ids, key=lambda x: str(x or "")):
            compradas_usuario = int(compras_por_usuario_org.get((org_id, u.id), 0)) if org_id else 0
            consumidas_usuario = int(consumidas_por_usuario_org.get((org_id, u.id), 0)) if org_id else 0
            saldo_empresa = max(0, int(compras_por_org.get(org_id, 0)) - int(consumidas_por_org.get(org_id, 0))) if org_id else 0
            cantidad_compras = sum(1 for c in compras_pagadas if c.usuario_id == u.id and c.organizacion_id == org_id)
            if u.rol.codigo == "RESPONSABLE_SST":
                estado_usuario = "EMPRESA_SIN_COMPRA" if not compras_por_org.get(org_id) else ("EMPRESA_AGOTADA" if saldo_empresa == 0 else "USA_SALDO_EMPRESA")
            elif cantidad_compras == 0:
                estado_usuario = "SIN_COMPRA_PROPIA" if not compras_por_org.get(org_id) else "SALDO_COMPARTIDO"
            else:
                estado_usuario = "AGOTADAS" if saldo_empresa == 0 else "DISPONIBLES"
            usuarios.append({
                "id": str(u.id),
                "nombre": _nombre(u),
                "correo": u.email,
                "rol": u.rol.codigo,
                "empresaId": str(org_id) if org_id else None,
                "empresa": nombres_org.get(org_id, "Sin empresa asociada"),
                "compras": cantidad_compras,
                "compradas": compradas_usuario,
                "consumidas": consumidas_usuario,
                "disponiblesEmpresa": saldo_empresa,
                "estado": estado_usuario,
                "ultimaCompra": ultima_compra_org[org_id].isoformat() if org_id in ultima_compra_org else None,
                "ultimaActividad": actividad_usuario_org[(org_id, u.id)].isoformat() if (org_id, u.id) in actividad_usuario_org else None,
            })


    movimientos = []
    for compra in compras_pagadas:
        pago_aprobado = max(
            (p for p in compra.pagos if p.estado == "APROBADO"),
            key=lambda p: p.procesado_en,
            default=None,
        )
        fecha = pago_aprobado.procesado_en if pago_aprobado else compra.creado_en
        movimientos.append({
            "id": f"compra-{compra.id}",
            "fecha": fecha.isoformat(),
            "tipo": "COMPRA",
            "empresa": nombres_org.get(compra.organizacion_id, "Sin empresa asociada"),
            "empresaId": str(compra.organizacion_id) if compra.organizacion_id else None,
            "usuario": nombres_usuario.get(compra.usuario_id, "Usuario no disponible"),
            "usuarioId": str(compra.usuario_id),
            "detalle": compra.plan_nombre or f"{compra.bateria_nombre} · tarifa por batería ${int(compra.tarifa_unitario or 0):,} COP",
            "cantidad": int(compra.cantidad or 0),
            "referencia": str(compra.id),
            "valor": float(compra.total or 0),
        })

    consumos_detalle = (
        db.query(Evaluacion, Usuario, Organizacion)
        .join(Usuario, Usuario.id == Evaluacion.evaluador_id)
        .join(Organizacion, Organizacion.id == Evaluacion.organizacion_id)
        .filter(Evaluacion.bateria_controlada.is_(True), Evaluacion.bateria_consumida_en.isnot(None))
        .order_by(Evaluacion.bateria_consumida_en.desc())
        .limit(1000)
        .all()
    )
    for fila in consumos_detalle:
        evaluacion, evaluador, organizacion = fila
        movimientos.append({
            "id": f"consumo-{evaluacion.id}",
            "fecha": evaluacion.bateria_consumida_en.isoformat(),
            "tipo": "CONSUMO",
            "empresa": organizacion.nombre,
            "empresaId": str(organizacion.id),
            "usuario": _nombre(evaluador),
            "usuarioId": str(evaluador.id),
            "detalle": "Consumo de 1 batería al guardar la primera respuesta de un enlace.",
            "cantidad": -1,
            "referencia": str(evaluacion.id),
            "valor": 0,
        })
    movimientos.sort(key=lambda m: m["fecha"], reverse=True)

    # El saldo global incluye únicamente compras asociadas a una empresa; las compras
    # sin organización se muestran aparte para no aparentar que pueden consumirse.
    total_compradas = sum(int(c.cantidad or 0) for c in compras_pagadas if c.organizacion_id)
    total_sin_empresa = sum(int(c.cantidad or 0) for c in compras_pagadas if not c.organizacion_id)
    total_consumidas = sum(int(cantidad or 0) for _, _, cantidad in consumos)
    total_disponibles = sum(e["disponibles"] for e in empresas)
    sin_compra = sum(1 for e in empresas if e["estado"] == "SIN_COMPRA")
    agotadas = sum(1 for e in empresas if e["estado"] == "AGOTADAS")
    por_agotarse = sum(1 for e in empresas if e["estado"] == "POR_AGOTARSE")
    return {
        "resumen": {
            "empresas": len(empresas),
            "bateriasCompradas": total_compradas,
            "bateriasConsumidas": total_consumidas,
            "bateriasDisponibles": total_disponibles,
            "bateriasSinEmpresa": total_sin_empresa,
            "empresasSinCompra": sin_compra,
            "empresasAgotadas": agotadas,
            "empresasPorAgotarse": por_agotarse,
            "movimientos": len(movimientos),
        },
        "empresas": empresas,
        "usuarios": usuarios,
        "movimientos": movimientos[:1000],
    }
