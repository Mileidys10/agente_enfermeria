# Nurse Agent - Agente Persistente de Notas de Enfermeria


## 🐳 Despliegue con Docker (Workstation Clínica Inmediata)

Para ejecutar la estación de enfermería completa sin instalar Python, Streamlit ni dependencias de ReportLab localmente:

```bash
# 1. Clonar el repositorio
git clone https://github.com/Mileidys10/agente_enfermeria.git
cd agente_enfermeria

# 2. Iniciar con Docker Compose
docker compose up --build
```

- 🌐 **Acceso Web:** [http://localhost:8501](http://localhost:8501)
- 💾 **Persistencia:** La base de datos SQLite y los reportes PDF se almacenan en `./data/`.
- 🔑 **API Key de Gemini / Gemma:** Puedes colocarla en la barra lateral de la interfaz o definir `GOOGLE_API_KEY` en tu `.env`.


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