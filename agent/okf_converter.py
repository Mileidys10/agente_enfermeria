# =============================================================
# agent/okf_converter.py
# Convierte el JSON de la nota de enfermería al formato
# OKF (Open Knowledge Format), implementado como JSON-LD.
#
# JSON-LD es la representación estándar de conocimiento abierto:
# - Usa @context para definir el vocabulario semántico
# - Cada campo tiene un significado universal y reutilizable
# - Compatible con Schema.org (estándar de la web semántica)
# - Interoperable con sistemas FHIR, OpenEHR, etc.
# =============================================================

# datetime: para generar fechas en formato ISO 8601 estándar
import datetime

# json: para guardar y leer archivos JSON-LD
import json

# os y Path: para manejo de rutas y creación de directorios
import os
from pathlib import Path


# ─────────────────────────────────────────────
# Contexto OKF / JSON-LD
# Define el vocabulario semántico del documento
# ─────────────────────────────────────────────
# Este contexto mapea cada campo del JSON a una URI semántica
# Esto hace que el documento sea "entendible" por máquinas de todo el mundo
OKF_CONTEXT = {
    # Vocabulario principal de la web semántica (Google, Bing, Yahoo lo usan)
    "@vocab": "https://schema.org/",

    # Prefijo para términos médicos de SNOMED CT (sistema internacional de codificación)
    "snomed": "http://snomed.info/id/",

    # Prefijo para términos de OpenEHR (estándar de registros de salud electrónicos)
    "openehr": "https://openehr.org/rm/",

    # Prefijo para términos FHIR (estándar de interoperabilidad de salud HL7)
    "fhir": "http://hl7.org/fhir/",

    # Mapeo de campos propios del schema de enfermería a URIs semánticas
    "vital_signs": "fhir:Observation",           # Los signos vitales son observaciones FHIR
    "blood_pressure": "snomed:75367002",          # Código SNOMED para presión arterial
    "heart_rate": "snomed:364075005",             # Código SNOMED para frecuencia cardíaca
    "temperature": "snomed:386725007",            # Código SNOMED para temperatura
    "oxygen_saturation": "snomed:59408-5",        # LOINC para SpO2
    "respiratory_rate": "snomed:86290005",        # Código SNOMED para frecuencia respiratoria
    "medications_given": "fhir:MedicationAdministration",  # Administración de medicamentos FHIR
    "interventions": "openehr:ACTION",            # Acciones de enfermería en OpenEHR
    "nursing_note": "openehr:COMPOSITION",        # Composición clínica en OpenEHR
}


# ─────────────────────────────────────────────
# Clase principal del convertidor OKF
# ─────────────────────────────────────────────
class OKFConverter:
    """
    Transforma un diccionario Python (nota de enfermería en JSON)
    a un documento OKF en formato JSON-LD semánticamente enriquecido.

    El resultado es un archivo .jsonld que puede ser:
    - Procesado por sistemas de salud compatibles con JSON-LD
    - Indexado por motores de conocimiento (RDF stores)
    - Interoperable con FHIR, OpenEHR, HL7
    """

    def __init__(self):
        """
        Constructor: lee la ruta de salida para archivos OKF desde .env
        """
        # Directorio donde se guardarán los archivos .jsonld generados
        self.okf_dir = Path(os.getenv("OKF_DIR", "./data/okf"))

        # Creamos el directorio si no existe
        self.okf_dir.mkdir(parents=True, exist_ok=True)

    def _build_patient_node(self, nota: dict) -> dict:
        """
        Construye el nodo semántico del paciente en JSON-LD.

        Args:
            nota: Diccionario con los datos de la nota

        Returns:
            Diccionario JSON-LD que representa al paciente
        """
        return {
            # @type define qué tipo de entidad es (Patient es de Schema.org/FHIR)
            "@type": "Patient",
            # @id es el identificador único del paciente en el grafo de conocimiento
            "@id": f"urn:patient:{nota.get('patient_id', 'unknown')}",
            # name es una propiedad de Schema.org Person (Patient hereda de Person)
            "name": nota.get("patient_name"),
            # Identificador interno del hospital
            "identifier": nota.get("patient_id"),
            # Sala y cama donde está internado
            "location": {
                "@type": "Place",
                "name": nota.get("ward"),
                "additionalProperty": {
                    "@type": "PropertyValue",
                    "name": "bed",
                    "value": nota.get("bed"),
                }
            }
        }

    def _build_vital_signs_node(self, vitals: dict | None) -> list:
        """
        Convierte los signos vitales a una lista de observaciones FHIR/JSON-LD.

        Cada signo vital se convierte en una "Observation" (observación clínica),
        que es la entidad estándar para mediciones de salud en FHIR.

        Args:
            vitals: Diccionario con los signos vitales (puede ser None)

        Returns:
            Lista de observaciones JSON-LD
        """
        # Si no hay signos vitales, devolvemos lista vacía
        if not vitals:
            return []

        # Lista donde acumularemos las observaciones
        observaciones = []

        # Mapeo de campo → (nombre legible, código SNOMED, unidad)
        mapeo_signos = {
            "blood_pressure": ("Presión Arterial", "snomed:75367002", "mmHg"),
            "heart_rate": ("Frecuencia Cardíaca", "snomed:364075005", "lpm"),
            "temperature": ("Temperatura", "snomed:386725007", "°C"),
            "oxygen_saturation": ("Saturación de Oxígeno", "snomed:59408-5", "%"),
            "respiratory_rate": ("Frecuencia Respiratoria", "snomed:86290005", "rpm"),
            "weight_kg": ("Peso", "snomed:27113001", "kg"),
            "height_cm": ("Talla", "snomed:50373000", "cm"),
        }

        # Iteramos sobre cada signo vital disponible
        for campo, (nombre, codigo, unidad) in mapeo_signos.items():
            valor = vitals.get(campo)  # Obtenemos el valor del campo

            # Solo incluimos los signos que tienen valor real (no null/None)
            if valor is not None:
                observaciones.append({
                    "@type": "Observation",               # Tipo FHIR: Observation
                    "name": nombre,                       # Nombre legible en español
                    "code": {"@id": codigo},              # Código semántico SNOMED
                    "value": valor,                       # Valor medido
                    "unitText": unidad,                   # Unidad de medida
                    "status": "final",                    # Estado de la observación (completada)
                })

        return observaciones

    def _build_medications_node(self, medicamentos: list | None) -> list:
        """
        Convierte la lista de medicamentos a nodos JSON-LD de tipo
        MedicationAdministration (administración de medicamento en FHIR).

        Args:
            medicamentos: Lista de diccionarios con datos de medicamentos

        Returns:
            Lista de nodos JSON-LD de medicamentos
        """
        # Si no hay medicamentos, devolvemos lista vacía
        if not medicamentos:
            return []

        # Transformamos cada medicamento a su representación semántica
        return [
            {
                "@type": "MedicalTherapy",  # Schema.org: terapia/tratamiento médico
                "drug": {
                    "@type": "Drug",         # Schema.org: medicamento
                    "name": med.get("name"),  # Nombre del medicamento
                    "dosageForm": med.get("dose"),   # Dosis administrada
                    "administrationRoute": med.get("route"),  # Vía de administración
                },
                "startTime": med.get("time"),  # Hora de administración
            }
            for med in medicamentos          # Un nodo por cada medicamento
        ]

    def convert(self, nota: dict, patient_id: str) -> dict:
        """
        Función principal: convierte una nota de enfermería completa a OKF/JSON-LD.

        El documento resultante es un grafo de conocimiento que describe:
        - Al paciente y su ubicación
        - La nota clínica con fecha y responsable
        - Los signos vitales como observaciones semánticas
        - Los medicamentos como terapias médicas
        - Las intervenciones y observaciones en texto

        Args:
            nota: Diccionario con los datos extraídos de la imagen
            patient_id: ID del paciente al que pertenece la nota

        Returns:
            Diccionario Python que representa el documento OKF/JSON-LD completo
        """
        # Construimos el documento JSON-LD raíz
        documento_okf = {
            # @context define el vocabulario semántico del documento
            "@context": OKF_CONTEXT,

            # @type define qué tipo de entidad es el documento raíz
            # MedicalRecord de Schema.org = registro médico completo
            "@type": "MedicalRecord",

            # @id es el identificador único de ESTA nota en el grafo
            # Usamos un URN con patient_id + fecha para unicidad
            "@id": (
                f"urn:nursing-note:{patient_id}:"
                f"{nota.get('date', datetime.date.today().isoformat())}"
            ),

            # Fecha de la nota en formato ISO 8601
            "dateCreated": nota.get("date"),

            # Hora de la nota
            "temporalCoverage": nota.get("time"),

            # Nombre del profesional que realizó la nota
            "author": {
                "@type": "Nurse",                        # Tipo personalizado: Enfermera
                "name": nota.get("nurse"),               # Nombre de la enfermera
                "jobTitle": "Enfermera Registrada",      # Título profesional
            },

            # Nodo del paciente (construido por _build_patient_node)
            "patient": self._build_patient_node(nota),

            # Signos vitales como lista de observaciones (nodos FHIR)
            "vitalSigns": self._build_vital_signs_node(nota.get("vital_signs")),

            # Medicamentos administrados (nodos MedicalTherapy)
            "medications": self._build_medications_node(nota.get("medications_given")),

            # Síntomas reportados como lista simple de texto
            "symptoms": nota.get("symptoms", []),

            # Observaciones clínicas en texto libre
            "clinicalObservations": nota.get("observations"),

            # Intervenciones realizadas (cambio de vendaje, etc.)
            "actions": nota.get("interventions", []),

            # Acciones pendientes para el siguiente turno
            "nextActions": nota.get("next_actions", []),

            # Escala de dolor EVA (0-10)
            "painScale": nota.get("pain_scale"),

            # Tipo de dieta prescrita
            "diet": nota.get("diet"),

            # Estado de movilidad del paciente
            "mobility": nota.get("mobility"),

            # Registro de eliminación
            "elimination": nota.get("elimination"),

            # Texto crudo de la imagen para trazabilidad
            "originalText": nota.get("raw_text"),

            # Metadata de generación del documento OKF
            "generatedAt": datetime.datetime.now().isoformat(),
            "formatVersion": "OKF/JSON-LD 1.0",
            "conformsTo": "https://schema.org/MedicalRecord",
        }

        return documento_okf

    def save(self, nota: dict, patient_id: str) -> Path:
        """
        Convierte la nota a OKF y la guarda como archivo .jsonld en disco.

        Args:
            nota: Diccionario con los datos de la nota
            patient_id: ID del paciente

        Returns:
            Path al archivo .jsonld guardado
        """
        # Convertimos la nota al formato OKF
        documento_okf = self.convert(nota, patient_id)

        # Generamos el nombre del archivo con patient_id y fecha actual
        # Esto garantiza unicidad si hay varias notas del mismo paciente
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_archivo = f"{patient_id}_{timestamp}.jsonld"

        # Construimos la ruta completa del archivo de salida
        ruta_salida = self.okf_dir / nombre_archivo

        # Escribimos el JSON-LD al archivo con codificación UTF-8
        # ensure_ascii=False preserva caracteres especiales como tildes (á, é, ñ)
        # indent=2 hace el archivo legible por humanos
        with open(ruta_salida, "w", encoding="utf-8") as f:
            json.dump(documento_okf, f, ensure_ascii=False, indent=2)

        return ruta_salida
