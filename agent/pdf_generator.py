# =============================================================
# agent/pdf_generator.py
# Genera un PDF profesional con el reporte de la nota de
# enfermería, usando la librería ReportLab.
#
# El PDF incluye:
# - Encabezado institucional (nombre del hospital, fecha, enfermera)
# - Tabla de signos vitales con colores
# - Medicamentos administrados
# - Síntomas e intervenciones
# - Observaciones clínicas en texto libre
# - Próximas acciones a realizar
# =============================================================

# datetime: para formatear fechas y horas en el PDF
import datetime

# os y Path: para manejo de rutas de archivos
import os
from pathlib import Path

# ── ReportLab: librería principal de generación de PDFs ──────
# SimpleDocTemplate: plantilla de documento con márgenes automáticos
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

# getSampleStyleSheet: estilos predefinidos de texto (Heading1, Normal, etc.)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# colors: paleta de colores para tablas, fondos y texto
from reportlab.lib import colors

# units.cm: conversión de centímetros a puntos PostScript (1cm = 28.35pt)
from reportlab.lib.units import cm

# pagesizes.A4: tamaño estándar de página en Europa y Latinoamérica
from reportlab.lib.pagesizes import A4

# Alineación de texto (LEFT, CENTER, RIGHT)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


# ─────────────────────────────────────────────
# Paleta de colores institucional del PDF
# ─────────────────────────────────────────────
# Color principal: azul médico para encabezados
COLOR_PRIMARIO = colors.HexColor("#1565C0")
# Color secundario: azul claro para fila de encabezado de tablas
COLOR_SECUNDARIO = colors.HexColor("#E3F2FD")
# Color de alerta: rojo suave para valores críticos
COLOR_ALERTA = colors.HexColor("#FFEBEE")
# Color de fondo alterno para filas de tabla (gris muy claro)
COLOR_FILA_ALTERNA = colors.HexColor("#F5F5F5")
# Blanco estándar
COLOR_BLANCO = colors.white


class PDFGenerator:
    """
    Genera reportes PDF profesionales de notas de enfermería.
    El PDF es el documento final que se archiva en el expediente
    del paciente y puede imprimirse o compartirse digitalmente.
    """

    def __init__(self):
        """
        Constructor: inicializa rutas y estilos de texto para el PDF.
        """
        # Directorio de salida para los PDFs (leído desde .env)
        self.pdf_dir = Path(os.getenv("PDF_DIR", "./data/pdf"))

        # Creamos el directorio si no existe
        self.pdf_dir.mkdir(parents=True, exist_ok=True)

        # Nombre del hospital (leído desde .env, aparece en el encabezado)
        self.hospital = os.getenv("HOSPITAL_NAME", "Hospital General")

        # Nombre de la enfermera responsable (leído desde .env)
        self.enfermera_default = os.getenv("NURSE_NAME", "Enfermera Responsable")

        # Cargamos los estilos predefinidos de ReportLab
        self.estilos = getSampleStyleSheet()

        # Definimos estilos personalizados adicionales para el documento
        self._definir_estilos()

    def _definir_estilos(self):
        """
        Define los estilos tipográficos personalizados del documento.
        ReportLab usa una hoja de estilos similar a CSS.
        """
        # Estilo para el título principal del hospital (grande, centrado, blanco)
        self.estilo_titulo = ParagraphStyle(
            name="TituloHospital",
            parent=self.estilos["Title"],      # Hereda del estilo Title base
            fontSize=18,                        # Tamaño de fuente en puntos
            textColor=COLOR_BLANCO,             # Texto blanco sobre fondo azul
            alignment=TA_CENTER,                # Centrado horizontalmente
            fontName="Helvetica-Bold",          # Fuente bold para mayor impacto
            spaceAfter=4,                       # Espacio después del párrafo (pts)
        )

        # Estilo para subtítulos de sección (ej. "Signos Vitales", "Medicamentos")
        self.estilo_seccion = ParagraphStyle(
            name="TituloSeccion",
            parent=self.estilos["Heading2"],
            fontSize=11,
            textColor=COLOR_PRIMARIO,           # Azul médico para diferenciarlo
            fontName="Helvetica-Bold",
            spaceBefore=12,                     # Espacio antes del título de sección
            spaceAfter=4,
        )

        # Estilo para texto normal del cuerpo del documento
        self.estilo_cuerpo = ParagraphStyle(
            name="Cuerpo",
            parent=self.estilos["Normal"],
            fontSize=10,
            leading=14,                         # Interlineado (espaciado entre líneas)
            textColor=colors.black,
        )

        # Estilo para listas de ítems (síntomas, intervenciones, etc.)
        self.estilo_lista = ParagraphStyle(
            name="ListaItem",
            parent=self.estilos["Normal"],
            fontSize=10,
            leading=13,
            leftIndent=15,                      # Sangría izquierda para efecto de lista
            bulletIndent=5,                     # Sangría del bullet
            textColor=colors.black,
        )

        # Estilo para el encabezado de tabla (texto blanco sobre azul)
        self.estilo_tabla_header = ParagraphStyle(
            name="TablaHeader",
            parent=self.estilos["Normal"],
            fontSize=9,
            fontName="Helvetica-Bold",
            textColor=COLOR_BLANCO,
            alignment=TA_CENTER,
        )

        # Estilo para datos en tabla
        self.estilo_tabla_dato = ParagraphStyle(
            name="TablaDato",
            parent=self.estilos["Normal"],
            fontSize=9,
            alignment=TA_CENTER,
        )

        # Estilo para el pie de página
        self.estilo_pie = ParagraphStyle(
            name="PiePagina",
            parent=self.estilos["Normal"],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER,
        )

    def _construir_encabezado(self, nota: dict) -> list:
        """
        Construye el encabezado institucional del PDF.
        Incluye: nombre del hospital, datos del paciente, fecha/hora y enfermera.

        Args:
            nota: Diccionario con los datos de la nota

        Returns:
            Lista de elementos ReportLab para el encabezado
        """
        elementos = []  # Lista donde acumulamos los bloques del PDF

        # ── Barra azul de título ──────────────────────────────
        # Tabla de 1 columna con fondo azul para el título del hospital
        tabla_titulo = Table(
            # Contenido: una celda con el nombre del hospital
            [[Paragraph(f"🏥 {self.hospital}", self.estilo_titulo)]],
            colWidths=[17 * cm],  # Ancho total = ancho de la página
        )
        tabla_titulo.setStyle(TableStyle([
            # Fondo azul médico para toda la fila de título
            ("BACKGROUND", (0, 0), (-1, -1), COLOR_PRIMARIO),
            # Padding interno de la celda
            ("TOPPADDING", (0, 0), (-1, -1), 12),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ]))
        elementos.append(tabla_titulo)

        # Subtítulo: "Nota de Enfermería" con la fecha
        subtitulo_texto = (
            "📋 NOTA DE ENFERMERÍA  |  "
            f"{nota.get('date', 'Sin fecha')} — {nota.get('time', '')}"
        )
        tabla_subtitulo = Table(
            [[Paragraph(subtitulo_texto, ParagraphStyle(
                name="Sub",
                parent=self.estilo_cuerpo,
                fontSize=9,
                textColor=colors.darkblue,
                alignment=TA_CENTER,
            ))]],
            colWidths=[17 * cm],
        )
        tabla_subtitulo.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), COLOR_SECUNDARIO),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        elementos.append(tabla_subtitulo)
        elementos.append(Spacer(1, 0.3 * cm))

        # ── Tabla de datos del paciente ───────────────────────
        # Datos básicos en una tabla de 4 columnas (etiqueta | valor)
        datos_paciente = [
            # Fila de encabezado de la tabla
            [
                Paragraph("PACIENTE", self.estilo_tabla_header),
                Paragraph("ID", self.estilo_tabla_header),
                Paragraph("ENFERMERA", self.estilo_tabla_header),
                Paragraph("SALA / CAMA", self.estilo_tabla_header),
            ],
            # Fila con los datos reales
            [
                Paragraph(str(nota.get("patient_name") or "—"), self.estilo_tabla_dato),
                Paragraph(str(nota.get("patient_id") or "—"), self.estilo_tabla_dato),
                Paragraph(str(nota.get("nurse") or self.enfermera_default), self.estilo_tabla_dato),
                Paragraph(
                    f"{nota.get('ward', '—')} / Cama {nota.get('bed', '—')}",
                    self.estilo_tabla_dato
                ),
            ],
        ]

        tabla_paciente = Table(datos_paciente, colWidths=[5 * cm, 3 * cm, 5 * cm, 4 * cm])
        tabla_paciente.setStyle(TableStyle([
            # Encabezado con fondo azul y texto blanco
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_PRIMARIO),
            ("TEXTCOLOR", (0, 0), (-1, 0), COLOR_BLANCO),
            # Datos con fondo blanco y borde
            ("BACKGROUND", (0, 1), (-1, -1), colors.white),
            # Borde alrededor de todas las celdas
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            # Alineación vertical centrada
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            # Padding interior
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        elementos.append(tabla_paciente)

        return elementos

    def _construir_signos_vitales(self, vitales: dict | None) -> list:
        """
        Construye la sección de signos vitales como una tabla visual.

        Args:
            vitales: Diccionario con los signos vitales o None

        Returns:
            Lista de elementos ReportLab para la sección
        """
        elementos = []  # Acumulador de elementos de esta sección

        # Título de la sección
        elementos.append(Paragraph("🩺 Signos Vitales", self.estilo_seccion))

        # Si no hay signos vitales, mostramos un mensaje indicativo
        if not vitales:
            elementos.append(Paragraph("No se registraron signos vitales.", self.estilo_cuerpo))
            return elementos

        # Definición de los campos a mostrar en la tabla
        # Formato: (etiqueta, clave_en_dict, unidad)
        campos_vitales = [
            ("TA (Presión Arterial)", "blood_pressure", "mmHg"),
            ("FC (Frecuencia Cardíaca)", "heart_rate", "lpm"),
            ("Temperatura", "temperature", "°C"),
            ("SpO₂ (Saturación O₂)", "oxygen_saturation", "%"),
            ("FR (Frecuencia Respiratoria)", "respiratory_rate", "rpm"),
            ("Peso", "weight_kg", "kg"),
            ("Talla", "height_cm", "cm"),
        ]

        # Encabezado de la tabla de signos vitales
        filas = [
            [
                Paragraph("Parámetro", self.estilo_tabla_header),
                Paragraph("Valor", self.estilo_tabla_header),
                Paragraph("Unidad", self.estilo_tabla_header),
            ]
        ]

        # Agregamos una fila por cada signo vital disponible
        for etiqueta, clave, unidad in campos_vitales:
            valor = vitales.get(clave)

            # Solo incluimos los signos que tienen valor registrado
            if valor is not None:
                filas.append([
                    Paragraph(etiqueta, self.estilo_cuerpo),
                    Paragraph(str(valor), self.estilo_tabla_dato),
                    Paragraph(unidad, self.estilo_tabla_dato),
                ])

        # Si no hay valores para ningún signo, mostramos mensaje vacío
        if len(filas) == 1:
            elementos.append(Paragraph("Signos vitales no legibles en la imagen.", self.estilo_cuerpo))
            return elementos

        # Construimos la tabla con columnas proporcionales
        tabla_sv = Table(filas, colWidths=[8 * cm, 5 * cm, 4 * cm])
        tabla_sv.setStyle(TableStyle([
            # Encabezado azul
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_PRIMARIO),
            ("TEXTCOLOR", (0, 0), (-1, 0), COLOR_BLANCO),
            # Filas alternas con color suave para mejor legibilidad
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COLOR_FILA_ALTERNA]),
            # Borde gris entre celdas
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            # Alineación vertical
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            # Padding de celdas
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        elementos.append(tabla_sv)

        return elementos

    def _construir_lista_simple(self, titulo: str, emoji: str, items: list | None, color_titulo=None) -> list:
        """
        Construye una sección genérica con título y lista de ítems con bullets.
        Se usa para síntomas, intervenciones y próximas acciones.

        Args:
            titulo: Texto del título de la sección
            emoji: Emoji decorativo para el título
            items: Lista de strings con los ítems
            color_titulo: Color del título (opcional, default COLOR_PRIMARIO)

        Returns:
            Lista de elementos ReportLab para la sección
        """
        elementos = []

        # Título de la sección con el emoji provisto
        elementos.append(Paragraph(f"{emoji} {titulo}", self.estilo_seccion))

        # Si no hay ítems, mostramos un guión
        if not items:
            elementos.append(Paragraph("—", self.estilo_cuerpo))
            return elementos

        # Creamos un párrafo con bullet (•) por cada ítem de la lista
        for item in items:
            elementos.append(
                Paragraph(f"• {item}", self.estilo_lista)
            )

        return elementos

    def _construir_medicamentos(self, medicamentos: list | None) -> list:
        """
        Construye la sección de medicamentos administrados como tabla.

        Args:
            medicamentos: Lista de diccionarios con los medicamentos

        Returns:
            Lista de elementos ReportLab para la sección
        """
        elementos = []

        # Título de la sección
        elementos.append(Paragraph("💊 Medicamentos Administrados", self.estilo_seccion))

        # Si no hay medicamentos, mostramos un mensaje
        if not medicamentos:
            elementos.append(Paragraph("Sin medicamentos registrados.", self.estilo_cuerpo))
            return elementos

        # Encabezado de la tabla de medicamentos
        filas = [
            [
                Paragraph("Medicamento", self.estilo_tabla_header),
                Paragraph("Dosis", self.estilo_tabla_header),
                Paragraph("Vía", self.estilo_tabla_header),
                Paragraph("Hora", self.estilo_tabla_header),
            ]
        ]

        # Una fila por cada medicamento administrado
        for med in medicamentos:
            filas.append([
                Paragraph(str(med.get("name") or "—"), self.estilo_cuerpo),
                Paragraph(str(med.get("dose") or "—"), self.estilo_tabla_dato),
                Paragraph(str(med.get("route") or "—"), self.estilo_tabla_dato),
                Paragraph(str(med.get("time") or "—"), self.estilo_tabla_dato),
            ])

        # Tabla de medicamentos con anchos de columna proporcionales
        tabla_meds = Table(filas, colWidths=[6 * cm, 4 * cm, 4 * cm, 3 * cm])
        tabla_meds.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_PRIMARIO),
            ("TEXTCOLOR", (0, 0), (-1, 0), COLOR_BLANCO),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COLOR_FILA_ALTERNA]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        elementos.append(tabla_meds)

        return elementos

    def generate(self, nota: dict, patient_id: str) -> Path:
        """
        Función principal: genera el PDF completo de la nota de enfermería.

        Orden del documento:
        1. Encabezado institucional (hospital, paciente, fecha, enfermera)
        2. Signos vitales (tabla)
        3. Síntomas (lista)
        4. Medicamentos (tabla)
        5. Escala de dolor + dieta + movilidad (inline)
        6. Observaciones clínicas (texto libre)
        7. Intervenciones (lista)
        8. Próximas acciones (lista)
        9. Pie de página

        Args:
            nota: Diccionario con los datos de la nota de enfermería
            patient_id: ID del paciente (para nombrar el archivo)

        Returns:
            Path al archivo PDF generado
        """
        # ── Generar nombre y ruta del archivo PDF ─────────────
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_archivo = f"{patient_id}_{timestamp}.pdf"
        ruta_pdf = self.pdf_dir / nombre_archivo

        # ── Crear el documento PDF con márgenes estándar ──────
        documento = SimpleDocTemplate(
            str(ruta_pdf),          # Ruta de salida como string
            pagesize=A4,            # Tamaño A4 (210 x 297 mm)
            rightMargin=1.5 * cm,   # Margen derecho de 1.5 cm
            leftMargin=1.5 * cm,    # Margen izquierdo de 1.5 cm
            topMargin=1.5 * cm,     # Margen superior de 1.5 cm
            bottomMargin=1.5 * cm,  # Margen inferior de 1.5 cm
        )

        # ── Construir la lista de elementos del PDF ────────────
        # ReportLab trabaja con una lista de "Flowables" (elementos que fluyen)
        # Los vamos acumulando en orden y ReportLab los renderiza automáticamente
        elementos = []

        # 1. Encabezado: hospital, paciente, fecha, enfermera
        elementos.extend(self._construir_encabezado(nota))
        elementos.append(Spacer(1, 0.4 * cm))  # Espacio vertical

        # 2. Signos vitales en tabla
        elementos.extend(self._construir_signos_vitales(nota.get("vital_signs")))
        elementos.append(Spacer(1, 0.3 * cm))

        # 3. Síntomas en lista con bullets
        elementos.extend(self._construir_lista_simple(
            "Síntomas Reportados", "🔴",
            nota.get("symptoms")
        ))
        elementos.append(Spacer(1, 0.3 * cm))

        # 4. Medicamentos administrados en tabla
        elementos.extend(self._construir_medicamentos(nota.get("medications_given")))
        elementos.append(Spacer(1, 0.3 * cm))

        # 5. Datos adicionales: escala de dolor, dieta, movilidad
        elementos.append(Paragraph("📊 Datos Adicionales", self.estilo_seccion))

        # Construimos texto inline con los campos adicionales disponibles
        datos_adicionales = []

        if nota.get("pain_scale") is not None:
            datos_adicionales.append(f"🔢 Escala de Dolor (EVA): <b>{nota['pain_scale']}/10</b>")

        if nota.get("diet"):
            datos_adicionales.append(f"🍽️ Dieta: <b>{nota['diet']}</b>")

        if nota.get("mobility"):
            datos_adicionales.append(f"🚶 Movilidad: <b>{nota['mobility']}</b>")

        if nota.get("elimination"):
            datos_adicionales.append(f"🔵 Eliminación: <b>{nota['elimination']}</b>")

        # Si hay datos adicionales, los mostramos; si no, un guión
        if datos_adicionales:
            for dato in datos_adicionales:
                elementos.append(Paragraph(dato, self.estilo_cuerpo))
        else:
            elementos.append(Paragraph("—", self.estilo_cuerpo))

        elementos.append(Spacer(1, 0.3 * cm))

        # 6. Observaciones clínicas en texto libre (área más larga)
        elementos.append(Paragraph("📝 Observaciones Clínicas", self.estilo_seccion))
        obs_texto = nota.get("observations") or "Sin observaciones registradas."

        # Usamos una tabla de 1 celda para encuadrar el texto de observaciones
        tabla_obs = Table(
            [[Paragraph(obs_texto, self.estilo_cuerpo)]],
            colWidths=[17 * cm],
        )
        tabla_obs.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 1, COLOR_SECUNDARIO),  # Borde azul claro
            ("BACKGROUND", (0, 0), (-1, -1), colors.white),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ]))
        elementos.append(tabla_obs)
        elementos.append(Spacer(1, 0.3 * cm))

        # 7. Intervenciones realizadas en lista
        elementos.extend(self._construir_lista_simple(
            "Intervenciones Realizadas", "⚕️",
            nota.get("interventions")
        ))
        elementos.append(Spacer(1, 0.3 * cm))

        # 8. Próximas acciones pendientes en lista
        elementos.extend(self._construir_lista_simple(
            "Próximas Acciones / Pendientes", "📌",
            nota.get("next_actions")
        ))
        elementos.append(Spacer(1, 0.5 * cm))

        # ── Línea separadora antes del pie ───────────────────
        elementos.append(HRFlowable(
            width="100%",
            thickness=1,
            color=colors.lightgrey
        ))
        elementos.append(Spacer(1, 0.2 * cm))

        # 9. Pie de página con metadata de generación
        pie_texto = (
            f"{self.hospital}  |  "
            f"Generado: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}  |  "
            f"Enfermera: {nota.get('nurse') or self.enfermera_default}  |  "
            f"ID Paciente: {patient_id}"
        )
        elementos.append(Paragraph(pie_texto, self.estilo_pie))

        # ── Renderizar el PDF ─────────────────────────────────
        # build() toma la lista de elementos y genera el archivo PDF en disco
        documento.build(elementos)

        return ruta_pdf
