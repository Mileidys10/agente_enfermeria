# ==============================================================================
# Dockerfile — Agente Clínico de Enfermería (Streamlit + ReportLab + OKF)
# Agente Clinico de Enfermeria - Contenedorizacion Docker
# ==============================================================================

FROM python:3.11-slim

LABEL maintainer="Mileidys10 <agamezmileidys@gmail.com>"
LABEL project="Agente Clínico de Enfermería"
LABEL version="1.1.0"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true

WORKDIR /app

# Instalar utilidades de sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente y módulos del agente
COPY agent/ ./agent/
COPY data/ ./data/
COPY app.py .
COPY main.py .

EXPOSE 8501

# Healthcheck nativo de Streamlit
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Comando por defecto para iniciar la estación clínica en Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
