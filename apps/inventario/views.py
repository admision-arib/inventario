import io
import os
import tempfile
from datetime import datetime

import requests
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.management import call_command
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

# ReportLab
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    BaseDocTemplate, Frame, HRFlowable, KeepTogether, PageTemplate,
    Paragraph, Spacer, Table, TableStyle
)

# Modelos y formularios locales
from .forms import CargaCSVForm, ComisionInventarioForm
from .models import ComisionInventario, TomaInventario
from apps.bienes.models.area import Area
from apps.bienes.models.bien import Bien

# Decoradores de permisos personalizados
from apps.usuarios.decorators import (
    gestionar_comisiones_requerido,
    escanear_inventario_requerido,
    ver_reportes_requerido,
)

# URL del logo institucional (usado en el acta PDF)
LOGO_URL = "https://iestparib.edu.pe/wp-content/uploads/2024/09/cropped-LOGO-ARIB-1.png"


# ============================
# LISTA DE COMISIONES
# (Todos los usuarios autenticados)
# ============================
@login_required
@gestionar_comisiones_requerido
def lista_comisiones(request):
    comisiones = ComisionInventario.objects.filter(activo=True).order_by('-fecha_inicio')
    return render(request, 'inventario/lista_comisiones.html', {'comisiones': comisiones})


# ============================
# CREAR COMISIÓN
# (ADMIN, CONTROL_PATRIMONIAL)
# ============================
@login_required
@gestionar_comisiones_requerido
def crear_comision(request):
    if request.method == 'POST':
        form = ComisionInventarioForm(request.POST)
        if form.is_valid():
            comision = form.save(commit=False)
            comision.save()
            form.save_m2m()  # importante para vocales
            messages.success(request, '✅ Comisión creada correctamente.')
            return redirect('lista_comisiones')
    else:
        form = ComisionInventarioForm()
    return render(request, 'inventario/form_comision.html', {'form': form})


# ============================
# CARGAR CSV Y EJECUTAR CONCILIACIÓN
# (ADMIN, CONTROL_PATRIMONIAL)
# ============================
@login_required
@gestionar_comisiones_requerido
def cargar_csv(request, pk):
    comision = get_object_or_404(ComisionInventario, pk=pk)

    if request.method == 'POST':
        form = CargaCSVForm(request.POST, request.FILES)
        if form.is_valid():
            archivo = request.FILES['archivo']
            ruta = None

            if not archivo.name.endswith('.csv'):
                messages.error(request, "❌ El archivo debe ser formato CSV.")
                return redirect('cargar_csv', pk=pk)

            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp:
                    for chunk in archivo.chunks():
                        tmp.write(chunk)
                    ruta = tmp.name

                call_command('conciliar_inventario', str(comision.id), ruta, verificado_por_id=request.user.id)
                messages.success(request, "✅ Conciliación ejecutada correctamente.")
            except Exception as e:
                messages.error(request, f"❌ Error al procesar archivo: {e}")
            finally:
                if ruta and os.path.exists(ruta):
                    os.unlink(ruta)

            return redirect('detalle_comision', pk=comision.id)
    else:
        form = CargaCSVForm()

    return render(request, 'inventario/cargar_csv.html', {'form': form, 'comision': comision})


# =============================
# DETALLE COMISION + DASHBOARD
# (ADMIN, CONTROL_PATRIMONIAL, INVENTARIADOR)
# =============================
@login_required
@escanear_inventario_requerido
def detalle_comision(request, pk):
    comision = get_object_or_404(ComisionInventario, pk=pk)
    area_id = request.GET.get('area')

    if area_id:
        bienes = Bien.objects.filter(area_id=area_id)
        tomas = TomaInventario.objects.filter(comision=comision, bien__area_id=area_id)
    else:
        bienes = Bien.objects.none()
        tomas = TomaInventario.objects.none()

    tomas_dict = {t.bien_id: t for t in tomas if t.bien}
    inventario = []

    for bien in bienes:
        toma = tomas_dict.get(bien.id)
        inventario.append({
            'codigo': bien.codigo_patrimonial,
            'denominacion': bien.denominacion,
            'estado': 'ENCONTRADO' if toma else 'NO_ENCONTRADO',
            'responsable': bien.usuario_responsable,
            'toma_id': toma.id if toma else None
        })

    total = len(inventario)
    encontrados = sum(1 for i in inventario if i['estado'] == 'ENCONTRADO')
    faltantes = total - encontrados
    sobrantes = tomas.filter(estado_verificacion='SOBRANTE').count()
    areas = Area.objects.all()

    return render(request, 'inventario/detalle.html', {
        'comision': comision,
        'inventario': inventario,
        'total': total,
        'encontrados': encontrados,
        'faltantes': faltantes,
        'sobrantes': sobrantes,
        'areas': areas,
        'area_id': area_id,
    })


# =====================
# ESCANEO QR (AJAX)
# (ADMIN, CONTROL_PATRIMONIAL, INVENTARIADOR)
# =====================
@login_required
@escanear_inventario_requerido
def escanear_bien(request):
    codigo = request.GET.get('codigo')
    comision_id = request.GET.get('comision')
    area_id = request.GET.get('area')

    if not codigo:
        return JsonResponse({'estado': 'ERROR'})

    comision = get_object_or_404(ComisionInventario, id=comision_id)
    bien = Bien.objects.filter(codigo_patrimonial=codigo).first()

    if not bien:
        return JsonResponse({'estado': 'INVALIDO'})

    if area_id and int(bien.area_id) != int(area_id):
        return JsonResponse({'estado': 'AREA_INVALIDA'})

    existe = TomaInventario.objects.filter(comision=comision, bien=bien).exists()
    if existe:
        return JsonResponse({'estado': 'REPETIDO'})

    TomaInventario.objects.create(
        comision=comision,
        codigo_verificado=codigo,
        bien=bien,
        estado_verificacion='ENCONTRADO',
        verificado_por=request.user,
        ubicacion_encontrada=bien.area.nombre
    )

    return JsonResponse({
        'estado': 'ENCONTRADO',
        'codigo': bien.codigo_patrimonial,
        'denominacion': bien.denominacion,
        'responsable': str(bien.usuario_responsable or "")
    })


# =====================
# ACTUALIZAR ESTADO (AJAX)
# =====================
@require_POST
@login_required
@escanear_inventario_requerido
def actualizar_estado(request):
    toma_id = request.POST.get('toma_id')
    estado = request.POST.get('estado')

    try:
        toma = TomaInventario.objects.get(id=toma_id)
        toma.estado_conservacion_verificado = estado
        toma.save()
        return JsonResponse({'ok': True})
    except TomaInventario.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Registro no encontrado'})


# =====================
# ACTA PDF
# (ADMIN, CONTROL_PATRIMONIAL, AUDITOR)
# =====================
def obtener_logo_institucional():
    if not hasattr(obtener_logo_institucional, "_cache_logo"):
        try:
            response = requests.get(LOGO_URL, timeout=5)
            if response.status_code == 200:
                obtener_logo_institucional._cache_logo = ImageReader(io.BytesIO(response.content))
            else:
                obtener_logo_institucional._cache_logo = None
        except Exception:
            obtener_logo_institucional._cache_logo = None
    return obtener_logo_institucional._cache_logo


class ActaDocTemplate(BaseDocTemplate):
    def __init__(self, filename, comision_nombre, **kwargs):
        super().__init__(filename, **kwargs)
        self.comision_nombre = comision_nombre
        frame_main = Frame(
            2 * cm, 2.5 * cm,
            A4[0] - 4 * cm, A4[1] - 5.5 * cm,
            id='main_frame'
        )
        self.addPageTemplates([
            PageTemplate(id='DocumentLayout', frames=[frame_main], onPage=self.draw_page_decorations)
        ])

    def draw_page_decorations(self, canvas, doc):
        canvas.saveState()
        page_w, page_h = A4

        # Línea superior institucional
        canvas.setStrokeColor(colors.HexColor('#1E3A8A'))
        canvas.setLineWidth(1.5)
        canvas.line(2 * cm, page_h - 2.5 * cm, page_w - 2 * cm, page_h - 2.5 * cm)

        # Logo institucional
        logo_img = obtener_logo_institucional()
        if logo_img:
            canvas.drawImage(logo_img, 2 * cm, page_h - 2.3 * cm, width=4.5 * cm, height=1.3 * cm,
                             preserveAspectRatio=True, mask='auto')
        else:
            canvas.setFont('Helvetica-Bold', 11)
            canvas.setFillColor(colors.HexColor('#1E3A8A'))
            canvas.drawString(2 * cm, page_h - 2.0 * cm, "IESTP ARIB")

        # Metadatos de la cabecera
        canvas.setFont('Helvetica-Bold', 8)
        canvas.setFillColor(colors.HexColor('#475569'))
        canvas.drawRightString(page_w - 2 * cm, page_h - 1.8 * cm, "SISTEMA DE INVENTARIO PATRIMONIAL")
        canvas.setFont('Helvetica', 7.5)
        canvas.drawRightString(page_w - 2 * cm, page_h - 2.2 * cm, f"Comisión: {self.comision_nombre.upper()}")

        # Pie de página
        canvas.setStrokeColor(colors.HexColor('#CBD5E1'))
        canvas.setLineWidth(0.5)
        canvas.line(2 * cm, 1.8 * cm, page_w - 2 * cm, 1.8 * cm)

        canvas.setFont('Helvetica', 7.5)
        canvas.setFillColor(colors.HexColor('#64748B'))
        fecha_emision = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        canvas.drawString(2 * cm, 1.3 * cm, f"Reporte Oficial emitido el: {fecha_emision} | Control Físico")
        canvas.drawCentredString(page_w / 2.0, 1.3 * cm, "Directiva N° 006-2021-EF")
        canvas.drawRightString(page_w - 2 * cm, 1.3 * cm, f"Página {doc.page}")
        canvas.restoreState()


@login_required
@ver_reportes_requerido
def acta_pdf(request, pk):
    comision = get_object_or_404(ComisionInventario, pk=pk)
    area_id = request.GET.get('area')

    # Consultas optimizadas
    tomas = TomaInventario.objects.filter(
        comision=comision,
        bien__isnull=False
    ).select_related('bien', 'bien__area', 'verificado_por')

    if area_id:
        tomas = tomas.filter(bien__area_id=area_id)
        bienes_area = Bien.objects.filter(area_id=area_id)
        area_obj = bienes_area.first().area if bienes_area.exists() else None
        area_nombre = area_obj.nombre if area_obj else "Área No Identificada"
    else:
        bienes_area = Bien.objects.none()
        area_nombre = "Todas las Áreas Institucionales"

    escaneados_ids = tomas.values_list('bien_id', flat=True)
    faltantes = bienes_area.exclude(id__in=escaneados_ids)

    buffer = io.BytesIO()

    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=14, leading=18,
        textColor=colors.HexColor('#0F172A'), alignment=TA_CENTER, spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=10.5, leading=14,
        textColor=colors.HexColor('#2563EB'), alignment=TA_CENTER, spaceAfter=15
    )
    meta_label = ParagraphStyle(
        'MetaLabel', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=9, leading=12, textColor=colors.HexColor('#334155')
    )
    meta_value = ParagraphStyle(
        'MetaValue', parent=styles['Normal'],
        fontName='Helvetica', fontSize=9, leading=12, textColor=colors.HexColor('#0F172A')
    )
    section_title = ParagraphStyle(
        'SectionTitle', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=11, leading=14,
        textColor=colors.HexColor('#1E3A8A'), spaceBefore=14, spaceAfter=8
    )
    th_style = ParagraphStyle(
        'TableHeaderText', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=8, leading=10,
        textColor=colors.white, alignment=TA_CENTER
    )
    td_style = ParagraphStyle(
        'TableCellText', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8, leading=10.5, textColor=colors.HexColor('#334155')
    )
    td_style_center = ParagraphStyle(
        'TableCellTextCenter', parent=td_style, alignment=TA_CENTER
    )
    kpi_title = ParagraphStyle(
        'KpiTitle', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=8.5, leading=11, textColor=colors.HexColor('#475569')
    )

    story = []
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph("INSTITUTO DE EDUCACIÓN SUPERIOR TECNOLÓGICO PÚBLICO ARIB", title_style))
    story.append(Paragraph("ACTA DE CONCILIACIÓN FÍSICA E INVENTARIO PATRIMONIAL", subtitle_style))

    # Panel de datos de la comisión
    resolucion_texto = getattr(comision, 'resolucion_designacion', getattr(comision, 'resolucion', 'No Especificada'))
    f_inicio = comision.fecha_inicio.strftime('%d/%m/%Y') if hasattr(comision.fecha_inicio, 'strftime') else str(comision.fecha_inicio)
    f_fin = comision.fecha_fin.strftime('%d/%m/%Y') if hasattr(comision.fecha_fin, 'strftime') else str(comision.fecha_fin)

    meta_data = [
        [Paragraph("Comisión Designada:", meta_label), Paragraph(str(comision.nombre), meta_value)],
        [Paragraph("Resolución / Doc:", meta_label), Paragraph(str(resolucion_texto), meta_value)],
        [Paragraph("Periodo de Vigencia:", meta_label), Paragraph(f"{f_inicio} hasta {f_fin}", meta_value)],
        [Paragraph("Cuadrante Geográfico:", meta_label), Paragraph(str(area_nombre), meta_value)]
    ]
    meta_table = Table(meta_data, colWidths=[4 * cm, 13 * cm])
    meta_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 12))

    # KPIs
    total_bienes = tomas.count() + faltantes.count()
    encontrados = tomas.filter(estado_verificacion__in=['ENCONTRADO', 'E']).count()
    no_encontrados = tomas.filter(estado_verificacion__in=['NO_ENCONTRADO', 'NE']).count()
    total_faltantes = faltantes.count()

    def build_kpi_cell(num, color_hex):
        return Paragraph(f'<font size="13" color="{color_hex}"><b>{num}</b></font>', td_style_center)

    kpi_data = [
        [Paragraph("Total Carga Cuadrante", kpi_title), Paragraph("Bienes Conciliados", kpi_title),
         Paragraph("Sobrantes / No Encontrados", kpi_title), Paragraph("Faltantes Críticos", kpi_title)],
        [build_kpi_cell(total_bienes, '#0F172A'), build_kpi_cell(encontrados, '#16A34A'),
         build_kpi_cell(no_encontrados, '#DC2626'), build_kpi_cell(total_faltantes, '#EA580C')]
    ]
    kpi_table = Table(kpi_data, colWidths=[4.25 * cm] * 4)
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F8FAFC')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(kpi_table)

    # Tabla de bienes verificados
    story.append(Paragraph("I. DETALLE DE BIENES FISICAMENTE VERIFICADOS (ESCANEADOS)", section_title))

    headers_tomas = [
        Paragraph("Item", th_style), Paragraph("Código SIGA / QR", th_style),
        Paragraph("Descripción del Activo", th_style), Paragraph("Área Operativa", th_style),
        Paragraph("Condición", th_style), Paragraph("Operador", th_style)
    ]
    table_tomas_data = [headers_tomas]
    for idx, t in enumerate(tomas, start=1):
        is_encontrado = t.estado_verificacion in ['ENCONTRADO', 'E']
        color_tag = '#16A34A' if is_encontrado else '#DC2626'
        label_tag = "ENCONTRADO" if is_encontrado else "FALTANTE"

        denominacion_bien = t.bien.denominacion if t.bien else "Bien no identificado"
        area_bien = str(t.bien.area.nombre) if t.bien and t.bien.area else "Sin Área"
        operador_nombre = t.verificado_por.get_full_name() if t.verificado_por and hasattr(t.verificado_por, 'get_full_name') else str(t.verificado_por)

        table_tomas_data.append([
            Paragraph(str(idx), td_style_center),
            Paragraph(str(t.codigo_verificado), td_style_center),
            Paragraph(str(denominacion_bien), td_style),
            Paragraph(str(area_bien), td_style_center),
            Paragraph(f'<font color="{color_tag}"><b>● {label_tag}</b></font>', td_style_center),
            Paragraph(str(operador_nombre), td_style)
        ])

    col_widths_tomas = [1.2 * cm, 3.2 * cm, 5.4 * cm, 2.8 * cm, 2.4 * cm, 2.5 * cm]
    tomas_table = Table(table_tomas_data, colWidths=col_widths_tomas, repeatRows=1)
    tomas_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A8A')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#F8FAFC'), colors.white]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(tomas_table)

    # Tabla de faltantes
    story.append(Paragraph("II. DIVISION DE BIENES FALTANTES (FALTAS DE CONCILIACIÓN FÍSICA)", section_title))

    if faltantes.exists():
        headers_faltantes = [
            Paragraph("Nro", th_style), Paragraph("Código Patrimonial", th_style),
            Paragraph("Descripción y Características del Activo", th_style),
            Paragraph("Área de Cargo Comprobado", th_style)
        ]
        table_falt_data = [headers_faltantes]

        for idx, b in enumerate(faltantes, start=1):
            cod_patrimonial = getattr(b, 'codigo_patrimonial', getattr(b, 'codigo', 'S/C'))
            table_falt_data.append([
                Paragraph(str(idx), td_style_center),
                Paragraph(str(cod_patrimonial), td_style_center),
                Paragraph(str(b.denominacion), td_style),
                Paragraph(str(b.area.nombre) if b.area else "Sin Asignar", td_style_center)
            ])

        col_widths_falt = [1.5 * cm, 4.0 * cm, 7.5 * cm, 4.5 * cm]
        falt_table = Table(table_falt_data, colWidths=col_widths_falt, repeatRows=1)
        falt_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#991B1B')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#FCA5A5')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#FEF2F2'), colors.white]),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(falt_table)
    else:
        story.append(Paragraph(
            '<font color="#16A34A"><i>Felicidades. No se registran inconsistencias ni activos faltantes en este cuadrante.</i></font>',
            td_style))

    # Firmas
    story.append(Spacer(1, 1.8 * cm))
    firma_titulos = []
    firma_lineas = []

    # Presidente
    if comision.presidente:
        nom_p = comision.presidente.get_full_name() if hasattr(comision.presidente, 'get_full_name') else getattr(comision.presidente, 'nombre_completo', str(comision.presidente))
        dni_p = getattr(comision.presidente, 'dni', '')
        firma_titulos.append(Paragraph(f"<b>{nom_p.upper()}</b><br/>DNI: {dni_p}<br/>Presidente de Comisión", td_style_center))
        firma_lineas.append(Paragraph("____________________________<br/>Firma Autorizada", td_style_center))
    else:
        firma_titulos.append(Paragraph("<b>PRESIDENTE DE COMISIÓN</b><br/>Especialista Responsable", td_style_center))
        firma_lineas.append(Paragraph("____________________________<br/>Firma", td_style_center))

    # Veedor
    if comision.veedor:
        nom_v = comision.veedor.get_full_name() if hasattr(comision.veedor, 'get_full_name') else getattr(comision.veedor, 'nombre_completo', str(comision.veedor))
        dni_v = getattr(comision.veedor, 'dni', '')
        firma_titulos.append(Paragraph(f"<b>{nom_v.upper()}</b><br/>DNI: {dni_v}<br/>Veedor / Órgano de Control", td_style_center))
        firma_lineas.append(Paragraph("____________________________<br/>Firma Autorizada", td_style_center))
    else:
        firma_titulos.append(Paragraph("<b>VEEDOR EXTERNO</b><br/>Órgano de Control de Activos", td_style_center))
        firma_lineas.append(Paragraph("____________________________<br/>Firma", td_style_center))

    table_firmas_data = [firma_lineas, [Spacer(1, 5), Spacer(1, 5)], firma_titulos]
    tabla_firmas = Table(table_firmas_data, colWidths=[8.5 * cm, 8.5 * cm])
    tabla_firmas.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(KeepTogether(tabla_firmas))

    # Construcción del PDF
    doc = ActaDocTemplate(
        buffer,
        comision_nombre=comision.nombre,
        pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=3 * cm, bottomMargin=3 * cm
    )
    doc.build(story)

    buffer.seek(0)
    filename_clean = f"Acta_Conciliacion_{comision.id}_{datetime.now().strftime('%Y%m%d')}.pdf"

    return HttpResponse(
        buffer,
        content_type='application/pdf',
        headers={'Content-Disposition': f'inline; filename="{filename_clean}"'}
    )