from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from django.utils import timezone

class ExportadorInformes:
    """
    Clase utilitaria para exportar informes a PDF y Excel
    """
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """
        Configurar estilos personalizados para los PDFs
        """
        # Estilo para el título principal
        self.styles.add(ParagraphStyle(
            name='TituloNexo',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            textColor=colors.HexColor('#39bfb2'),
            alignment=1  # Centrado
        ))
        
        # Estilo para subtítulos
        self.styles.add(ParagraphStyle(
            name='SubtituloNexo',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.HexColor('#F28627')
        ))
    
    def generar_pdf_inventario(self, datos, usuario):
        """
        Generar PDF para el informe de inventario general
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        
        # Encabezado del reporte
        story.append(Paragraph("NEXO – Sistema de Gestión de Inventario", self.styles['TituloNexo']))
        story.append(Paragraph("Reporte de Inventario General", self.styles['SubtituloNexo']))
        story.append(Spacer(1, 12))
        
        # Información del reporte
        info_reporte = f"""
        <b>Usuario que genera:</b> {usuario.empleado_nombre or usuario.nombreusuario}<br/>
        <b>Fecha y hora de generación:</b> {timezone.now().strftime('%d/%m/%Y %H:%M:%S')}<br/>
        <b>Total de productos:</b> {datos['resumen']['total_productos']}<br/>
        <b>Total de existencias:</b> {datos['resumen']['total_existencias']}<br/>
        <b>Productos con stock bajo:</b> {datos['resumen']['productos_bajo_stock']}<br/>
        <b>Valor total del inventario:</b> ${datos['resumen']['valor_total']:,.2f}
        """
        story.append(Paragraph(info_reporte, self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Tabla de productos
        data = [['Código', 'Producto', 'Categoría', 'Ubicación', 'Existencia', 'Precio', 'Valor Total']]
        
        for producto in datos['productos']:
            valor_total = producto.existenciaproducto * (producto.precioproducto or 0)
            data.append([
                producto.id_producto,
                producto.nombreproducto,
                producto.idcategoriapro.nombrecategoria if producto.idcategoriapro else 'Sin categoría',
                producto.idubicacionpro.nombreubicacion,
                str(producto.existenciaproducto),
                f"${producto.precioproducto or 0:.2f}",
                f"${valor_total:.2f}"
            ])
        
        # Crear tabla
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#39bfb2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        
        # Construir PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    def generar_pdf_ventas(self, datos, usuario, fecha_inicio, fecha_fin):
        """
        Generar PDF para el informe de ventas
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        
        # Encabezado del reporte
        story.append(Paragraph("NEXO – Sistema de Gestión de Inventario", self.styles['TituloNexo']))
        story.append(Paragraph("Reporte de Ventas", self.styles['SubtituloNexo']))
        story.append(Spacer(1, 12))
        
        # Información del reporte
        periodo = ""
        if fecha_inicio and fecha_fin:
            periodo = f"<b>Período:</b> {fecha_inicio.strftime('%d/%m/%Y')} - {fecha_fin.strftime('%d/%m/%Y')}<br/>"
        
        info_reporte = f"""
        <b>Usuario que genera:</b> {usuario.empleado_nombre or usuario.nombreusuario}<br/>
        <b>Fecha y hora de generación:</b> {timezone.now().strftime('%d/%m/%Y %H:%M:%S')}<br/>
        {periodo}
        <b>Total de ventas:</b> {datos['resumen']['total_ventas']}<br/>
        <b>Monto total:</b> ${datos['resumen']['monto_total']:,.2f}<br/>
        <b>Promedio por venta:</b> ${datos['resumen']['promedio_venta']:,.2f}
        """
        story.append(Paragraph(info_reporte, self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Tabla de ventas
        data = [['ID Venta', 'Fecha', 'Cliente', 'Vendedor', 'Total', 'Estado']]
        
        for venta in datos['ventas']:
            cliente_nombre = venta.codcliente.idpersonacliente.nombre_completo if venta.codcliente and venta.codcliente.idpersonacliente else 'Cliente no especificado'
            vendedor_nombre = venta.idusuarioventa.empleado_nombre or venta.idusuarioventa.nombreusuario if venta.idusuarioventa else 'No especificado'
            
            data.append([
                str(venta.id_venta),
                venta.fechaventa.strftime('%d/%m/%Y %H:%M') if venta.fechaventa else 'No especificada',
                cliente_nombre,
                vendedor_nombre,
                f"${venta.total or 0:.2f}",
                venta.estado
            ])
        
        # Crear tabla
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#39bfb2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        
        # Construir PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    def generar_excel_inventario(self, datos):
        """
        Generar archivo Excel para el informe de inventario
        """
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Inventario General"
        
        # Configurar estilos
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="39BFB2", end_color="39BFB2", fill_type="solid")
        center_alignment = Alignment(horizontal="center")
        
        # Encabezados
        headers = ['Código', 'Producto', 'Categoría', 'Ubicación', 'Existencia', 'Precio', 'Valor Total']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = center_alignment
        
        # Datos
        for row, producto in enumerate(datos['productos'], 2):
            valor_total = producto.existenciaproducto * (producto.precioproducto or 0)
            
            ws.cell(row=row, column=1, value=producto.id_producto)
            ws.cell(row=row, column=2, value=producto.nombreproducto)
            ws.cell(row=row, column=3, value=producto.idcategoriapro.nombrecategoria if producto.idcategoriapro else 'Sin categoría')
            ws.cell(row=row, column=4, value=producto.idubicacionpro.nombreubicacion)
            ws.cell(row=row, column=5, value=producto.existenciaproducto)
            ws.cell(row=row, column=6, value=float(producto.precioproducto or 0))
            ws.cell(row=row, column=7, value=float(valor_total))
        
        # Ajustar ancho de columnas
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        # Guardar en buffer
        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()
    
    def generar_excel_ventas(self, datos):
        """
        Generar archivo Excel para el informe de ventas
        """
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Reporte de Ventas"
        
        # Configurar estilos
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="39BFB2", end_color="39BFB2", fill_type="solid")
        center_alignment = Alignment(horizontal="center")
        
        # Encabezados
        headers = ['ID Venta', 'Fecha', 'Cliente', 'Vendedor', 'Total', 'Estado']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = center_alignment
        
        # Datos
        for row, venta in enumerate(datos['ventas'], 2):
            cliente_nombre = venta.codcliente.idpersonacliente.nombre_completo if venta.codcliente and venta.codcliente.idpersonacliente else 'Cliente no especificado'
            vendedor_nombre = venta.idusuarioventa.empleado_nombre or venta.idusuarioventa.nombreusuario if venta.idusuarioventa else 'No especificado'
            
            ws.cell(row=row, column=1, value=venta.id_venta)
            ws.cell(row=row, column=2, value=venta.fechaventa.strftime('%d/%m/%Y %H:%M') if venta.fechaventa else 'No especificada')
            ws.cell(row=row, column=3, value=cliente_nombre)
            ws.cell(row=row, column=4, value=vendedor_nombre)
            ws.cell(row=row, column=5, value=float(venta.total or 0))
            ws.cell(row=row, column=6, value=venta.estado)
        
        # Ajustar ancho de columnas
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        # Guardar en buffer
        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()
