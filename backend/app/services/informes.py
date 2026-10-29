import hashlib
import os
import secrets
import uuid
from sqlalchemy.orm import Session, contains_eager, joinedload
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

from app.core.roles import ROLES_EVALUADOR
from app.core.config import get_settings
from app.core.crypto import utcnow
from app.core.errors import AppError
from app.models.evaluation import Evaluacion, EvaluacionParticipante, ResultadoDimension, Informe
from app.models.organization import Organizacion
from app.models.survey import Recomendacion
from app.models.user import Usuario

settings = get_settings()


def _asegurar_directorio_storage() -> str:
    path = os.path.join(settings.storage_path, "informes")
    os.makedirs(path, exist_ok=True)
    return path


def _calcular_sha256(file_path: str) -> str:
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha.update(chunk)
    return sha.hexdigest()


def _url_verificacion(codigo: str) -> str:
    base = settings.frontend_url.rstrip("/")
    return f"{base}/verificar-informe/{codigo}"


def _bloque_verificacion(codigo: str, cell_style) -> list:
    from reportlab.platypus import KeepTogether
    from reportlab.graphics import renderPDF
    url = _url_verificacion(codigo)
    qr = QrCodeWidget(url)
    bounds = qr.getBounds()
    ancho = bounds[2] - bounds[0]
    alto = bounds[3] - bounds[1]
    escala = 72 / max(ancho, alto)
    drawing = Drawing(escala * ancho, escala * alto)
    drawing.add(qr)
    drawing.transform = (escala, 0, 0, escala, 0, 0)
    elementos = [
        HRFlowable(width="100%", thickness=0.5, color=colors.grey),
        Spacer(1, 6),
        Paragraph("<b>Verificación de autenticidad</b>", cell_style),
        Spacer(1, 4),
        Paragraph(f"Código: <font name='Courier'>{codigo}</font>", cell_style),
        Spacer(1, 4),
        drawing,
        Spacer(1, 4),
        Paragraph(f"Consulte la validez en: {url}", cell_style),
        Spacer(1, 6),
    ]
    return [KeepTogether(elementos)]


def generar_informe_individual(
    db: Session,
    evaluacion_id: uuid.UUID,
    participante_id: uuid.UUID,
    generado_por: uuid.UUID,
) -> Informe:
    participante = (
        db.query(EvaluacionParticipante)
        .options(
            joinedload(EvaluacionParticipante.trabajador),
            joinedload(EvaluacionParticipante.evaluacion).joinedload(Evaluacion.organizacion),
            joinedload(EvaluacionParticipante.resultados).joinedload(ResultadoDimension.dimension),
        )
        .filter(
            EvaluacionParticipante.evaluacion_id == evaluacion_id,
            EvaluacionParticipante.id == participante_id,
        )
        .first()
    )

    if participante is None:
        raise AppError(404, "Participante o evaluación no encontrado.")

    if participante.estado != "COMPLETADA" or not participante.resultados:
        raise AppError(400, "El participante no ha completado la evaluación o no existen resultados calculados.")

    dir_path = _asegurar_directorio_storage()
    filename = f"informe_individual_{participante.id}_{uuid.uuid4().hex[:6]}.pdf"
    file_path = os.path.join(dir_path, filename)

    codigo_verificacion = secrets.token_urlsafe(16)
    file_path_tmp = file_path + ".tmp"
    try:
        doc = SimpleDocTemplate(
            file_path_tmp,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#1E3A8A"),
            alignment=1,
        )
        subtitle_style = ParagraphStyle(
            "DocSubtitle",
            parent=styles["Normal"],
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#475569"),
            alignment=1,
        )
        section_style = ParagraphStyle(
            "SectionHeading",
            parent=styles["Heading2"],
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#1E293B"),
            spaceBefore=12,
            spaceAfter=6,
        )
        normal_style = styles["Normal"]
        cell_style = ParagraphStyle("TableCellInd", parent=normal_style, fontSize=8.5, leading=11)
        cell_bold_style = ParagraphStyle("TableCellBoldInd", parent=normal_style, fontSize=8.5, leading=11, fontName="Helvetica-Bold")
        cell_center_style = ParagraphStyle("TableCellCenterInd", parent=cell_style, alignment=1)
        header_cell_style = ParagraphStyle("HeaderCellInd", parent=normal_style, fontSize=8.5, leading=11, textColor=colors.HexColor("#1E3A8A"), fontName="Helvetica-Bold", alignment=1)

        story = []

        story.append(Paragraph("INFORME INDIVIDUAL DE RIESGO PSICOSOCIAL", title_style))
        story.append(Spacer(1, 4))
        story.append(Paragraph("Batería de Riesgo Psicosocial — Res. 2764 de 2022", subtitle_style))
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1E3A8A")))
        story.append(Spacer(1, 10))

        trabajador = participante.trabajador
        org = participante.evaluacion.organizacion
        datos_tabla = [
            [Paragraph("Trabajador:", cell_bold_style), Paragraph(f"{trabajador.nombre} {trabajador.apellido}", cell_style)],
            [Paragraph("Identificación:", cell_bold_style), Paragraph(f"{trabajador.numero_identificacion or 'N/A'}", cell_style)],
            [Paragraph("Cargo:", cell_bold_style), Paragraph(f"{trabajador.cargo or 'N/A'}", cell_style)],
            [Paragraph("Organización:", cell_bold_style), Paragraph(f"{org.nombre} (NIT: {org.nit})", cell_style)],
            [Paragraph("Evaluación:", cell_bold_style), Paragraph(f"{participante.evaluacion.nombre}", cell_style)],
            [Paragraph("Fecha de Cierre:", cell_bold_style), Paragraph(f"{participante.fecha_fin.strftime('%Y-%m-%d %H:%M') if participante.fecha_fin else 'N/A'}", cell_style)],
        ]
        t_datos = Table(datos_tabla, colWidths=[120, 420])
        t_datos.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(t_datos)
        story.append(Spacer(1, 14))

        story.append(Paragraph("Resultados Evaluados por Dimensión", section_style))

        res_headers = [
            Paragraph("Dimensión", header_cell_style),
            Paragraph("Dominio", header_cell_style),
            Paragraph("Puntaje Bruto", header_cell_style),
            Paragraph("Puntaje Transf.", header_cell_style),
            Paragraph("Nivel de Riesgo", header_cell_style),
        ]
        res_rows = [res_headers]

        color_nivel_map = {
            "SIN_RIESGO": colors.HexColor("#059669"),
            "BAJO": colors.HexColor("#1D4ED8"),
            "MEDIO": colors.HexColor("#B45309"),
            "ALTO": colors.HexColor("#C2410C"),
            "MUY_ALTO": colors.HexColor("#B91C1C"),
        }

        nivel_styles = {
            nivel: ParagraphStyle(f"Nivel_{nivel}", parent=cell_style, textColor=color, fontName="Helvetica-Bold", alignment=1)
            for nivel, color in color_nivel_map.items()
        }

        for res in sorted(participante.resultados, key=lambda r: r.dimension.orden):
            dim = res.dimension
            n_style = nivel_styles.get(res.nivel, cell_center_style)
            res_rows.append([
                Paragraph(dim.nombre, cell_style),
                Paragraph(dim.dominio, cell_style),
                Paragraph(str(res.puntaje_bruto), cell_center_style),
                Paragraph(f"{res.puntaje_transformado:.1f}", cell_center_style),
                Paragraph(res.nivel.replace("_", " "), n_style),
            ])

        t_res = Table(res_rows, colWidths=[155, 135, 70, 80, 100])
        t_res.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F1F5F9")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('PADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(t_res)

        # Recomendaciones de Intervención (Res. 2764 de 2022)
        story.append(Spacer(1, 14))
        story.append(Paragraph("Recomendaciones de Intervención (Res. 2764 de 2022)", section_style))

        has_recs = False
        for res in sorted(participante.resultados, key=lambda r: r.dimension.orden):
            recs = (
                db.query(Recomendacion)
                .filter(Recomendacion.dimension_id == res.dimension_id, Recomendacion.nivel == res.nivel)
                .order_by(Recomendacion.prioridad.asc())
                .all()
            )
            for rec in recs:
                has_recs = True
                story.append(Paragraph(f"• <b>[{res.dimension.nombre} — {res.nivel.replace('_', ' ')}]</b> <b>{rec.titulo}:</b> {rec.descripcion}", cell_style))
                story.append(Spacer(1, 4))

        if not has_recs:
            story.append(Paragraph("No existen recomendaciones de intervención específicas para los niveles actuales.", cell_style))

        story.extend(_bloque_verificacion(codigo_verificacion, cell_style))
        doc.build(story)
        os.replace(file_path_tmp, file_path)
    finally:
        if os.path.exists(file_path_tmp):
            try:
                os.remove(file_path_tmp)
            except OSError:
                pass

    hash_archivo = _calcular_sha256(file_path)
    informe_obj = Informe(
        evaluacion_id=evaluacion_id,
        tipo="INDIVIDUAL",
        formato="PDF",
        trabajador_id=participante.trabajador_id,
        ruta_archivo=file_path,
        generado_por=generado_por,
        generado_en=utcnow(),
        anonimizado=False,
        codigo_verificacion=codigo_verificacion,
        hash_sha256=hash_archivo,
    )
    db.add(informe_obj)
    db.commit()
    db.refresh(informe_obj)
    return informe_obj


def _serializar_informe(informe: Informe) -> dict:
    evaluacion = informe.evaluacion
    return {
        "id": str(informe.id),
        "evaluacionId": str(informe.evaluacion_id),
        "evaluacionNombre": evaluacion.nombre,
        "organizacionId": str(evaluacion.organizacion_id),
        "organizacionNombre": evaluacion.organizacion.nombre,
        "tipo": informe.tipo,
        "formato": informe.formato,
        "areaId": str(informe.area_id) if informe.area_id else None,
        "generadoEn": informe.generado_en.isoformat(),
        "anonimizado": informe.anonimizado,
        "codigoVerificacion": informe.codigo_verificacion,
        "hashSha256": informe.hash_sha256,
    }


def listar_informes(
    db: Session,
    actual: Usuario,
    evaluacion_id: uuid.UUID | None = None,
    tipo: str | None = None,
) -> list[dict]:
    """Lista los informes visibles para el usuario, con el mismo alcance que la descarga.

    - ADMINISTRADOR: informes de todas las organizaciones.
    - EVALUADOR_SST: informes de su propia organizacion.
    - TRABAJADOR: unicamente sus propios informes individuales.
    """
    query = (
        db.query(Informe)
        .join(Informe.evaluacion)
        .options(contains_eager(Informe.evaluacion).joinedload(Evaluacion.organizacion))
    )

    rol = actual.rol.codigo
    if rol == "SUPER_ADMINISTRADOR":
        pass
    elif rol in ROLES_EVALUADOR:
        query = query.filter(Evaluacion.organizacion_id == actual.organizacion_id)
    elif rol == "ADMINISTRADOR":
        # Informes agrupados de las empresas que creó.
        query = query.filter(
            Evaluacion.organizacion_id.in_(
                db.query(Organizacion.id).filter(Organizacion.creada_por_id == actual.id)
            ),
            Informe.tipo == "AGRUPADO",
        )
    elif rol == "TRABAJADOR":
        query = query.filter(Informe.tipo == "INDIVIDUAL", Informe.trabajador_id == actual.id)
    else:
        raise AppError(403, "No tiene permisos para consultar informes.")

    if evaluacion_id is not None:
        query = query.filter(Informe.evaluacion_id == evaluacion_id)
    if tipo is not None:
        query = query.filter(Informe.tipo == tipo.upper())

    informes = query.order_by(Informe.generado_en.desc()).all()
    return [_serializar_informe(informe) for informe in informes]


def obtener_verificacion_informe(db: Session, codigo: str) -> dict:
    """Verifica la autenticidad de un informe a partir de su código. Endpoint público."""
    informe = (
        db.query(Informe)
        .options(joinedload(Informe.evaluacion).joinedload(Evaluacion.organizacion))
        .filter(Informe.codigo_verificacion == codigo)
        .first()
    )
    if informe is None:
        raise AppError(404, "Código de verificación no encontrado.")

    hash_actual = _calcular_sha256(informe.ruta_archivo) if os.path.exists(informe.ruta_archivo) else None
    valido = hash_actual is not None and hash_actual == informe.hash_sha256

    return {
        "valido": valido,
        "tipo": informe.tipo,
        "formato": informe.formato,
        "organizacionNombre": informe.evaluacion.organizacion.nombre,
        "evaluacionNombre": informe.evaluacion.nombre,
        "generadoEn": informe.generado_en.isoformat(),
        "anonimizado": informe.anonimizado,
        "hashSha256": informe.hash_sha256,
    }
