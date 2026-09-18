import os
import uuid
from sqlalchemy.orm import Session, joinedload

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from openpyxl import Workbook

from app.core.config import get_settings
from app.core.crypto import utcnow
from app.core.errors import AppError
from app.models.evaluation import Evaluacion, EvaluacionParticipante, ResultadoDimension, Informe
from app.models.organization import Area, Organizacion
from app.models.survey import Dimension, Recomendacion
from app.models.user import Usuario

settings = get_settings()

def _asegurar_directorio_storage() -> str:
    path = os.path.join(settings.storage_path, "informes")
    os.makedirs(path, exist_ok=True)
    return path


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

    doc = SimpleDocTemplate(
        file_path,
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

    doc.build(story)

    informe_obj = Informe(
        evaluacion_id=evaluacion_id,
        tipo="INDIVIDUAL",
        formato="PDF",
        trabajador_id=participante.trabajador_id,
        ruta_archivo=file_path,
        generado_por=generado_por,
        generado_en=utcnow(),
        anonimizado=False,
    )
    db.add(informe_obj)
    db.commit()
    db.refresh(informe_obj)
    return informe_obj


def generar_informe_agrupado(
    db: Session,
    evaluacion_id: uuid.UUID,
    area_id: uuid.UUID | None,
    generado_por: uuid.UUID,
    formato: str = "PDF",
) -> Informe:
    evaluacion = db.query(Evaluacion).filter(Evaluacion.id == evaluacion_id).first()
    if evaluacion is None:
        raise AppError(404, "Evaluación no encontrada.")

    query = (
        db.query(EvaluacionParticipante)
        .options(
            joinedload(EvaluacionParticipante.trabajador),
            joinedload(EvaluacionParticipante.resultados).joinedload(ResultadoDimension.dimension),
        )
        .filter(
            EvaluacionParticipante.evaluacion_id == evaluacion_id,
            EvaluacionParticipante.estado == "COMPLETADA",
        )
    )

    if area_id:
        query = query.join(Usuario, Usuario.id == EvaluacionParticipante.trabajador_id).filter(Usuario.area_id == area_id)

    participantes = query.all()
    num_participantes = len(participantes)

    if num_participantes < settings.min_grupo_anonimato:
        raise AppError(
            400,
            f"No se puede generar el informe agrupado. El grupo tiene {num_participantes} participantes completados, "
            f"lo cual es inferior al mínimo requerido de anonimato ({settings.min_grupo_anonimato} personas).",
        )

    dimensiones = db.query(Dimension).filter(Dimension.version_id == evaluacion.version_id).order_by(Dimension.orden).all()
    
    agregados = []
    for dim in dimensiones:
        puntajes = []
        conteo_niveles = {"SIN_RIESGO": 0, "BAJO": 0, "MEDIO": 0, "ALTO": 0, "MUY_ALTO": 0}
        for p in participantes:
            res_dim = next((r for r in p.resultados if r.dimension_id == dim.id), None)
            if res_dim:
                puntajes.append(res_dim.puntaje_transformado)
                if res_dim.nivel in conteo_niveles:
                    conteo_niveles[res_dim.nivel] += 1
        prom = sum(puntajes) / len(puntajes) if puntajes else 0.0
        agregados.append({
            "dimensionId": dim.id,
            "dimension": dim.nombre,
            "dominio": dim.dominio,
            "promedio": round(prom, 2),
            "niveles": conteo_niveles,
        })

    dir_path = _asegurar_directorio_storage()
    formato_upper = formato.upper()

    if formato_upper == "EXCEL":
        filename = f"informe_agrupado_{evaluacion_id}_{uuid.uuid4().hex[:6]}.xlsx"
        file_path = os.path.join(dir_path, filename)
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Resumen Agrupado"

        ws.append(["Informe Agrupado de Riesgo Psicosocial"])
        ws.append([f"Evaluación: {evaluacion.nombre}"])
        ws.append([f"Total Participantes: {num_participantes}"])
        ws.append([])
        ws.append(["Dimensión", "Dominio", "Promedio Transformado (0-100)", "Sin Riesgo", "Bajo", "Medio", "Alto", "Muy Alto"])

        for agg in agregados:
            n = agg["niveles"]
            ws.append([
                agg["dimension"],
                agg["dominio"],
                agg["promedio"],
                n["SIN_RIESGO"],
                n["BAJO"],
                n["MEDIO"],
                n["ALTO"],
                n["MUY_ALTO"],
            ])
        wb.save(file_path)
    else:
        filename = f"informe_agrupado_{evaluacion_id}_{uuid.uuid4().hex[:6]}.pdf"
        file_path = os.path.join(dir_path, filename)
        
        doc = SimpleDocTemplate(file_path, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle("DocTitle", parent=styles["Heading1"], fontSize=18, leading=22, textColor=colors.HexColor("#1E3A8A"), alignment=1)
        subtitle_style = ParagraphStyle("DocSubtitle", parent=styles["Normal"], fontSize=11, leading=14, textColor=colors.HexColor("#475569"), alignment=1)
        section_style = ParagraphStyle("SectionHeading", parent=styles["Heading2"], fontSize=13, leading=16, textColor=colors.HexColor("#1E293B"), spaceBefore=12, spaceAfter=6)
        normal_style = styles["Normal"]
        cell_style = ParagraphStyle("TableCellAgr", parent=normal_style, fontSize=8.5, leading=11)
        cell_center_style = ParagraphStyle("TableCellCenterAgr", parent=cell_style, alignment=1)
        header_cell_style = ParagraphStyle("HeaderCellAgr", parent=normal_style, fontSize=8.5, leading=11, textColor=colors.HexColor("#1E3A8A"), fontName="Helvetica-Bold", alignment=1)

        story = [
            Paragraph("INFORME AGRUPADO DE RIESGO PSICOSOCIAL", title_style),
            Spacer(1, 4),
            Paragraph(f"<b>Evaluación:</b> {evaluacion.nombre} &nbsp;|&nbsp; <b>Total Participantes:</b> {num_participantes} (Anonimizado)", subtitle_style),
            Spacer(1, 10),
            HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1E3A8A")),
            Spacer(1, 12),
            Paragraph("Distribución de Riesgo y Promedios por Dimensión", section_style),
        ]

        table_data = [[
            Paragraph("Dimensión", header_cell_style),
            Paragraph("Dominio", header_cell_style),
            Paragraph("Prom. Transf.", header_cell_style),
            Paragraph("Sin Riesgo", header_cell_style),
            Paragraph("Bajo", header_cell_style),
            Paragraph("Medio", header_cell_style),
            Paragraph("Alto", header_cell_style),
            Paragraph("Muy Alto", header_cell_style),
        ]]

        for agg in agregados:
            n = agg["niveles"]
            table_data.append([
                Paragraph(agg["dimension"], cell_style),
                Paragraph(agg["dominio"], cell_style),
                Paragraph(f"{agg['promedio']:.1f}", cell_center_style),
                Paragraph(str(n["SIN_RIESGO"]), cell_center_style),
                Paragraph(str(n["BAJO"]), cell_center_style),
                Paragraph(str(n["MEDIO"]), cell_center_style),
                Paragraph(str(n["ALTO"]), cell_center_style),
                Paragraph(str(n["MUY_ALTO"]), cell_center_style),
            ])

        t = Table(table_data, colWidths=[145, 135, 50, 42, 42, 42, 42, 42])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F1F5F9")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('PADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(t)

        # Recomendaciones de Intervención Colectiva
        story.append(Spacer(1, 14))
        story.append(Paragraph("Recomendaciones de Intervención Colectiva (Res. 2764 de 2022)", section_style))

        has_recs = False
        for agg in agregados:
            n = agg["niveles"]
            # Determinar el nivel predominante o crítico de la dimensión
            if n["ALTO"] + n["MUY_ALTO"] > 0 or agg["promedio"] >= 50.0:
                nivel_prioridad = "MUY_ALTO" if n["MUY_ALTO"] > 0 else "ALTO"
            elif n["MEDIO"] > 0:
                nivel_prioridad = "MEDIO"
            else:
                nivel_prioridad = "BAJO"

            recs = (
                db.query(Recomendacion)
                .filter(Recomendacion.dimension_id == agg["dimensionId"], Recomendacion.nivel == nivel_prioridad)
                .order_by(Recomendacion.prioridad.asc())
                .all()
            )
            for rec in recs:
                has_recs = True
                story.append(Paragraph(f"• <b>[{agg['dimension']} — Enfoque {nivel_prioridad.replace('_', ' ')}]</b> <b>{rec.titulo}:</b> {rec.descripcion}", cell_style))
                story.append(Spacer(1, 4))

        if not has_recs:
            story.append(Paragraph("No se requieren recomendaciones de intervención colectiva urgente.", cell_style))

        doc.build(story)

    informe_obj = Informe(
        evaluacion_id=evaluacion_id,
        tipo="AGRUPADO",
        formato=formato_upper,
        area_id=area_id,
        ruta_archivo=file_path,
        generado_por=generado_por,
        generado_en=utcnow(),
        anonimizado=True,
    )
    db.add(informe_obj)
    db.commit()
    db.refresh(informe_obj)
    return informe_obj
