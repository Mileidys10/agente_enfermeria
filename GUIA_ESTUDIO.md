# Guía de Estudio: Agente de Enfermería con Gemini y Streamlit

¡Felicidades! Has construido un sistema completo que une Inteligencia Artificial multimodal (visión y audio) con estándares de salud (OKF/JSON-LD) y una interfaz de usuario interactiva. 

Esta guía te explica qué hace cada pieza del rompecabezas y qué debes estudiar para dominarlo por tu cuenta.

---

## 1. Arquitectura del Proyecto

El proyecto está dividido en dos partes principales:
1.  **El Backend (Lógica y Agente):** Carpeta `agent/`. Aquí vive la conexión con Gemini (`gemma_vision.py`), la conversión de datos de salud a estándares (`okf_converter.py`), la generación del PDF (`pdf_generator.py`) y la base de datos SQLite (`persistence.py`).
2.  **El Frontend (Interfaz UI):** Archivo `app.py`. Es la interfaz web construida con Streamlit que permite interactuar con el agente (subir fotos, grabar voz, ver el historial).

---

## 2. Conceptos Clave y Qué Estudiar

Para entender completamente este código y poder modificarlo o crear los tuyos propios, te recomiendo estudiar estos 4 pilares:

### A. Streamlit (La Interfaz Web)
Streamlit permite hacer aplicaciones web completas usando solo Python, sin saber HTML o JavaScript.
*   **Qué hace en el proyecto:** Crea la barra lateral (`st.sidebar`), las pestañas (`st.tabs`), lee el micrófono (`st.audio_input`), muestra los JSONs y permite descargar los PDFs.
*   **Qué debes estudiar:**
    *   *Concepto de ejecución top-down:* Streamlit corre el código de arriba a abajo cada vez que interactúas con la pantalla.
    *   *Manejo de estado (Session State):* Cómo recordar variables entre recargas.
    *   *Caché (`@st.cache_resource`):* Lo usamos para no reconectar la base de datos o recargar herramientas pesadas en cada clic.
    *   **Recurso recomendado:** [Documentación oficial de Streamlit (Get Started)](https://docs.streamlit.io/get-started)

### B. Gemini API (El Cerebro de IA)
Usamos el SDK oficial de Google (`google-genai`) para comunicarnos con el modelo de IA.
*   **Qué hace en el proyecto:** 
    *   Toma la foto (Visión) o el audio (Voz) y el prompt de instrucciones, y extrae un JSON estructurado.
    *   Usamos `gemini-3.7-flash` con la **Interactions API** (`client.interactions.create`) para el audio, ya que es la forma moderna de enviar archivos multimedia en Base64.
*   **Qué debes estudiar:**
    *   *Prompt Engineering (Ingeniería de Prompts):* Cómo pedirle a la IA exactamente lo que quieres (ver `EXTRACTION_PROMPT` en `json_schema.py`).
    *   *Multimodalidad:* Cómo pasar imágenes y audio (codificación en bytes y Base64) junto con el texto.
    *   *Structured Outputs (JSON):* Cómo forzar a la IA a responder en formato JSON que Python pueda entender (usando `json.loads`).
    *   **Recurso recomendado:** [Google AI Studio - Gemini API Docs](https://ai.google.dev/docs)

### C. Estándares de Salud y JSON-LD (OKF)
Los datos médicos no pueden estar "sueltos", deben seguir vocabularios estándar.
*   **Qué hace en el proyecto:** El `OKFConverter` toma el JSON simple de Gemini y le agrega un `@context` que mapea los campos a `Schema.org`, `SNOMED CT` (signos vitales) y `FHIR` (observaciones). Esto lo convierte en JSON-LD (Open Knowledge Format).
*   **Qué debes estudiar:**
    *   *Diccionarios en Python (`dict`):* Manipulación de datos clave-valor.
    *   *JSON-LD:* Cómo la web semántica vincula datos.
    *   *Conceptos básicos de interoperabilidad:* Saber qué es HL7 FHIR y SNOMED.

### D. Persistencia y Generación de Archivos
*   **Qué hace en el proyecto:** `sqlite3` guarda el historial de pacientes permanentemente en `data/nurse_agent.db`. `reportlab` dibuja el archivo PDF.
*   **Qué debes estudiar:**
    *   *SQLite3 en Python:* Consultas básicas (`SELECT`, `INSERT`, `UPDATE`).
    *   *Generación de PDFs:* Librería `ReportLab` (conceptos de Canvas, coordenadas X/Y para dibujar texto e imágenes).

---

## 3. Resumen de Flujo de Datos (Paso a Paso)

Cuando una enfermera presiona "Procesar voz con Gemini", esto es lo que ocurre internamente:

1.  **`app.py`:** `st.audio_input` captura tu voz a través del micrófono del navegador y lo convierte en bytes (audio WAV).
2.  **`app.py`:** Llama a `agente.analyze_audio(bytes_del_audio)`.
3.  **`gemma_vision.py`:** Convierte los bytes de audio a formato `Base64` (texto seguro para enviar por internet).
4.  **`gemma_vision.py`:** Llama a `client.interactions.create`, enviando el texto (Prompt) y el audio (Base64) a los servidores de Google (Gemini 3.7 Flash).
5.  **`gemma_vision.py`:** Gemini devuelve un JSON en formato texto. Python lo limpia y lo convierte a un Diccionario usando `json.loads()`.
6.  **`app.py`:** Toma ese diccionario y ejecuta el pipeline:
    *   Llama a `okf_converter.save()` para generar el `.jsonld`.
    *   Llama a `pdf_generator.generate()` para dibujar el PDF.
    *   Llama a `db.save_note()` para guardar todo en la base de datos local SQLite.
7.  **`app.py`:** La pantalla se actualiza, mostrando las tarjetas de métricas, el JSON, y habilitando los botones de descarga.

¡Sigue explorando el código fuente! Cada archivo está documentado línea por línea en español para que entiendas exactamente qué hace cada instrucción.
