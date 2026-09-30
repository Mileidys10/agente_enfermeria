# Nurse Agent - Agente Persistente de Notas de Enfermeria

Sistema de IA que ayuda a enfermeras a digitalizar notas manuscritas usando Gemma.
Pipeline: Imagen -> JSON -> OKF (JSON-LD) -> PDF -> SQLite

## Instalacion

pip install -r requirements.txt
copy .env.example .env
# Editar .env y agregar GOOGLE_API_KEY

## Uso

# Procesar imagen nueva
python main.py process --image foto_nota.jpg --patient-id P001

# Actualizar paciente existente (persistente)
python main.py update --image nueva_nota.jpg --patient-id P001

# Ver historial
python main.py history --patient-id P001

# Listar todos los pacientes
python main.py list-patients

# Regenerar PDF
python main.py export-pdf --patient-id P001
