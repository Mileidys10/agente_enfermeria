# =============================================================
# agent/json_schema.py
# Define la estructura de datos de una nota de enfermería.
# Centraliza el schema en un solo lugar para que todos los
# módulos usen el mismo formato esperado.
# =============================================================

# Importamos typing para anotar los tipos de cada campo
from typing import TypedDict, List, Optional


# ─────────────────────────────────────────────
# Signos vitales del paciente
# ─────────────────────────────────────────────
class VitalSigns(TypedDict, total=False):
    """
    Diccionario con los signos vitales del paciente.
    Todos los campos son opcionales (total=False) porque
    no todas las notas incluyen todos los signos.
    """
    blood_pressure: str        # Presión arterial, ej. "120/80 mmHg"
    heart_rate: int            # Frecuencia cardíaca en latidos/min
    temperature: float         # Temperatura corporal en °C
    oxygen_saturation: float   # Saturación de oxígeno en porcentaje (SpO2)
    respiratory_rate: int      # Frecuencia respiratoria en respiraciones/min
    weight_kg: float           # Peso en kilogramos (opcional)
    height_cm: float           # Talla en centímetros (opcional)


# ─────────────────────────────────────────────
# Medicamento administrado
# ─────────────────────────────────────────────
class Medication(TypedDict, total=False):
    """
    Representa un medicamento que fue administrado al paciente
    durante el turno de la enfermera.
    """
    name: str      # Nombre del medicamento, ej. "Paracetamol"
    dose: str      # Dosis, ej. "500 mg"
    route: str     # Vía de administración: oral, IV, IM, subcutánea...
    time: str      # Hora de administración en formato HH:MM


# ─────────────────────────────────────────────
# Nota de Enfermería completa (schema raíz)
# ─────────────────────────────────────────────
class NursingNote(TypedDict, total=False):
    """
    Schema completo de una nota de enfermería.
    Este es el formato JSON que el agente Gemma produce
    al analizar la imagen escrita a mano.

    Todos los campos son opcionales (total=False) porque
    una nota manuscrita puede estar incompleta.
    """
    patient_id: str                      # ID único del paciente (asignado por la enfermera o sistema)
    patient_name: str                    # Nombre completo del paciente
    date: str                            # Fecha de la nota en formato ISO 8601 (YYYY-MM-DD)
    time: str                            # Hora de la nota en formato HH:MM
    nurse: str                           # Nombre de la enfermera que escribe la nota
    ward: str                            # Sala o área hospitalaria (ej. "UCI", "Pediatría")
    bed: str                             # Número de cama del paciente
    vital_signs: VitalSigns              # Objeto con los signos vitales (ver arriba)
    symptoms: List[str]                  # Lista de síntomas reportados
    medications_given: List[Medication]  # Lista de medicamentos administrados
    observations: str                    # Texto libre con observaciones de la enfermera
    interventions: List[str]             # Intervenciones realizadas (ej. "Cambio de vendaje")
    next_actions: List[str]              # Acciones pendientes para el siguiente turno
    pain_scale: Optional[int]            # Escala de dolor del 0 al 10 (EVA)
    diet: Optional[str]                  # Tipo de dieta: normal, blanda, líquida, NPO...
    elimination: Optional[str]           # Registro de eliminación urinaria/fecal
    mobility: Optional[str]              # Estado de movilidad: deambula, reposo, sedado...
    raw_text: Optional[str]              # Texto crudo extraído de la imagen (para auditoría)


# ─────────────────────────────────────────────
# Prompt base que se enviará a Gemma para
# analizar la imagen y producir JSON
# ─────────────────────────────────────────────
EXTRACTION_PROMPT = """
Eres un asistente de enfermería médica especializado en leer notas manuscritas.
Analiza la imagen proporcionada que contiene una nota de enfermería escrita a mano.

Extrae TODA la información visible y devuelve un JSON válido con esta estructura exacta:
{
  "patient_id": "ID del paciente si es visible, sino null",
  "patient_name": "nombre completo del paciente",
  "date": "fecha en formato YYYY-MM-DD",
  "time": "hora en formato HH:MM",
  "nurse": "nombre de la enfermera",
  "ward": "sala o área hospitalaria",
  "bed": "número de cama",
  "vital_signs": {
    "blood_pressure": "presión arterial como string, ej. '120/80'",
    "heart_rate": número entero o null,
    "temperature": número decimal o null,
    "oxygen_saturation": número decimal o null,
    "respiratory_rate": número entero o null,
    "weight_kg": número decimal o null,
    "height_cm": número decimal o null
  },
  "symptoms": ["síntoma1", "síntoma2"],
  "medications_given": [
    {"name": "nombre", "dose": "dosis", "route": "vía", "time": "hora"}
  ],
  "observations": "texto de observaciones generales",
  "interventions": ["intervención1", "intervención2"],
  "next_actions": ["acción1", "acción2"],
  "pain_scale": número del 0 al 10 o null,
  "diet": "tipo de dieta o null",
  "elimination": "registro de eliminación o null",
  "mobility": "estado de movilidad o null",
  "raw_text": "transcripción literal de todo el texto que ves en la imagen"
}

REGLAS IMPORTANTES:
- Devuelve SOLO el JSON, sin texto adicional ni markdown (sin ```json).
- Si un campo no está visible en la imagen, usa null.
- Interpreta abreviaturas médicas comunes en español (TA=tensión arterial, FC=frecuencia cardíaca, etc.).
- Si la nota es ilegible en alguna parte, escríbelo en 'observations'.
- El JSON debe ser válido y parseable por Python json.loads().
"""
