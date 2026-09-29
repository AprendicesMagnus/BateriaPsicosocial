import os
import uuid
from sqlalchemy.orm import Session, contains_eager, joinedload

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
        raise AppError(404, "Participante o evaluaciÃ³n no encontrado.")

    if participante.estado != "COMPLETADA" or not participante.resultados:
        raise AppError(400, "El participante no ha completado la evaluaciÃ³n o no existen resultados calculados.")

    dir_path = _asegurar_directorio_storage()
    filename = f"informe_individual_{participante.id}_{uuid.uuid4().hex[:6]}.pdf"
    file_path = os.path.join(dir_path, filename)

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
        story.append(Paragraph("BaterÃ­a de Riesgo Psicosocial â€” Res. 2764 de 2022", subtitle_style))
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1E3A8A")))
        story.append(Spacer(1, 10))

        trabajador = participante.trabajador
        org = participante.evaluacion.organizacion
        datos_tabla = [
            [Paragraph("Trabajador:", cell_bold_style), Paragraph(f"{trabajador.nombre} {trabajador.apellido}", cell_style)],
            [Paragraph("IdentificaciÃ³n:", cell_bold_style), Paragraph(f"{trabajador.numero_identificacion or 'N/A'}", cell_style)],
            [Paragraph("Cargo:", cell_bold_style), Paragraph(f"{trabajador.cargo or 'N/A'}", cell_style)],
            [Paragraph("OrganizaciÃ³n:", cell_bold_style), Paragraph(f"{org.nombre} (NIT: {org.nit})", cell_style)],
            [Paragraph("EvaluaciÃ³n:", cell_bold_style), Paragraph(f"{participante.evaluacion.nombre}", cell_style)],
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

        story.append(Paragraph("Resultados Evaluados por DimensiÃ³n", section_style))

        res_headers = [
            Paragraph("DimensiÃ³n", header_cell_style),
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

        # Recomendaciones de IntervenciÃ³n (Res. 2764 de 2022)
        story.append(Spacer(1, 14))
        story.append(Paragraph("Recomendaciones de IntervenciÃ³n (Res. 2764 de 2022)", section_style))

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
                story.append(Paragraph(f"â€¢ <b>[{res.dimension.nombre} â€” {res.nivel.replace('_', ' ')}]</b> <b>{rec.titulo}:</b> {rec.descripcion}", cell_style))
                story.append(Spacer(1, 4))

        if not has_recs:
            story.append(Paragraph("No existen recomendaciones de intervenciÃ³n especÃ­ficas para los niveles actuales.", cell_style))

        doc.build(story)
        os.replace(file_path_tmp, file_path)
    finally:
        if os.path.exists(file_path_tmp):
            try:
                os.remove(file_path_tmp)
            except OSError:
                pass

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
        raise AppError(404, "EvaluaciÃ³n no encontrada.")

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
            f"lo cual es inferior al mÃ­nimo requerido de anonimato ({settings.min_grupo_anonimato} personas).",
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
    extension = "xlsx" if formato_upper == "EXCEL" else "pdf"
    filename = f"informe_agrupado_{evaluacion_id}_{uuid.uuid4().hex[:6]}.{extension}"
    file_path = os.path.join(dir_path, filename)
    file_path_tmp = file_path + ".tmp"

    try:
        if formato_upper == "EXCEL":
            from openpyxl.chart import BarChart, Reference
            from openpyxl.worksheet.table import Table, TableStyleInfo
            from openpyxl.styles import Font, PatternFill, Alignment

            wb = Workbook()
            ws = wb.active
            ws.title = "Resumen Agrupado"

            ws.append(["Informe Agrupado de Riesgo Psicosocial"])
            ws.append([f"Evaluaci\u00f3n: {evaluacion.nombre}"])
            ws.append([f"Total Participantes: {num_participantes}"])
            ws.append([])

            cabeceras = ["Dimensi\u00f3n", "Dominio", "Promedio Transformado (0-100)", "Sin Riesgo", "Bajo", "Medio", "Alto", "Muy Alto"]
            ws.append(cabeceras)
            header_row = ws.max_row
            header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
            header_font = Font(bold=True, color="FFFFFF")
            for cell in ws[header_row]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center", vertical="center")

            data_start_row = header_row + 1
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
            data_end_row = ws.max_row

            ws.column_dimensions["A"].width = 40
            ws.column_dimensions["B"].width = 30
            for col_letter in ["C", "D", "E", "F", "G", "H"]:
                ws.column_dimensions[col_letter].width = 18

            if data_end_row >= data_start_row:
                tabla_ref = f"A{header_row}:H{data_end_row}"
                tabla = Table(displayName="TablaDimensiones", ref=tabla_ref)
                estilo_tabla = TableStyleInfo(
                    name="TableStyleMedium2",
                    showFirstColumn=False,
                    showLastColumn=False,
                    showRowStripes=True,
                    showColumnStripes=False,
                )
                tabla.tableStyleInfo = estilo_tabla
                ws.add_table(tabla)

            # Hoja de grafico de barras con distribucion de niveles
            ws_chart = wb.create_sheet(title="Resumen gr\u00e1fico")

            ws_chart.append(["Dimensi\u00f3n", "Sin Riesgo", "Bajo", "Medio", "Alto", "Muy Alto"])
            for cell in ws_chart[1]:
                cell.font = Font(bold=True)

            for agg in agregados:
                n = agg["niveles"]
                ws_chart.append([
                    agg["dimension"],
                    n["SIN_RIESGO"],
                    n["BAJO"],
                    n["MEDIO"],
                    n["ALTO"],
                    n["MUY_ALTO"],
                ])

            chart_data_end = ws_chart.max_row
            chart = BarChart()
            chart.type = "col"
            chart.grouping = "clustered"
            chart.title = "Distribuci\u00f3n de Niveles de Riesgo por Dimensi\u00f3n"
            chart.y_axis.title = "Cantidad"
            chart.x_axis.title = "Dimensi\u00f3n"
            chart.style = 10
            chart.width = 30
            chart.height = 18

            data_ref = Reference(ws_chart, min_col=2, max_col=6, min_row=1, max_row=chart_data_end)
            cats = Reference(ws_chart, min_col=1, min_row=2, max_row=chart_data_end)
            chart.add_data(data_ref, titles_from_data=True)
            chart.set_categories(cats)

            colores_nivel = ["059669", "1D4ED8", "B45309", "C2410C", "B91C1C"]
            for idx_c, color in enumerate(colores_nivel):
                if idx_c < len(chart.series):
                    chart.series[idx_c].graphicalProperties.solidFill = color

            ws_chart.add_chart(chart, "A" + str(chart_data_end + 3))
            ws_chart.column_dimensions["A"].width = 40
            for col_letter in ["B", "C", "D", "E", "F"]:
                ws_chart.column_dimensions[col_letter].width = 14

            wb.save(file_path_tmp)
            os.replace(file_path_tmp, file_path)
        else:
            doc = SimpleDocTemplate(file_path_tmp, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
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
                Paragraph(f"<b>EvaluaciÃ³n:</b> {evaluacion.nombre} &nbsp;|&nbsp; <b>Total Participantes:</b> {num_participantes} (Anonimizado)", subtitle_style),
                Spacer(1, 10),
                HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1E3A8A")),
                Spacer(1, 12),
                Paragraph("DistribuciÃ³n de Riesgo y Promedios por DimensiÃ³n", section_style),
            ]

            table_data = [[
                Paragraph("DimensiÃ³n", header_cell_style),
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

            # Recomendaciones de IntervenciÃ³n Colectiva
            story.append(Spacer(1, 14))
            story.append(Paragraph("Recomendaciones de IntervenciÃ³n Colectiva (Res. 2764 de 2022)", section_style))

            has_recs = False
            for agg in agregados:
                n = agg["niveles"]
                # Determinar el nivel predominante o crÃ­tico de la dimensiÃ³n
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
                    story.append(Paragraph(f"â€¢ <b>[{agg['dimension']} â€” Enfoque {nivel_prioridad.replace('_', ' ')}]</b> <b>{rec.titulo}:</b> {rec.descripcion}", cell_style))
                    story.append(Spacer(1, 4))

            if not has_recs:
                story.append(Paragraph("No se requieren recomendaciones de intervenciÃ³n colectiva urgente.", cell_style))

            doc.build(story)
            os.replace(file_path_tmp, file_path)
    finally:
        if os.path.exists(file_path_tmp):
            try:
                os.remove(file_path_tmp)
            except OSError:
                pass

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
    elif rol == "EVALUADOR_SST":
        query = query.filter(Evaluacion.organizacion_id == actual.organizacion_id)
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


