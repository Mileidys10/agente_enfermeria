# =============================================================
# app.py — Interfaz web con Streamlit para el Agente de Enfermería
#
# Corre la app con:   streamlit run app.py
# Se abre en:         http://localhost:8501
#
# La app permite:
#   - Ingresar la API key manualmente (sin tocar el .env)
#   - Subir una imagen de nota manuscrita  → Gemma extrae JSON
#   - Grabar audio de voz dictando la nota → Gemma transcribe y extrae JSON
#   - Ver el JSON extraído en tiempo real
#   - Descargar el OKF (JSON-LD) y el PDF generados
#   - Ver el historial persistente de pacientes
# =============================================================

# streamlit: framework que convierte Python en una app web
import streamlit as st

# pathlib: manejo de rutas de archivos multiplataforma
from pathlib import Path

# os: setear variables de entorno desde la UI (sin tocar el .env)
import os

# tempfile: guardar la imagen subida en disco temporalmente para Pillow
import tempfile

# dotenv: carga el .env como base; la UI puede sobreescribir en memoria
from dotenv import load_dotenv

# Cargamos el .env al inicio (solo rellena lo que NO esté ya en el entorno)
load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=False)


# ─────────────────────────────────────────────
# Configuración de la página — debe ser lo PRIMERO en ejecutarse
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Agente de Enfermería",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ─────────────────────────────────────────────
# CSS personalizado para estilo visual consistente
# ─────────────────────────────────────────────
st.markdown("""
<style>
    h1 { color: #1565C0; font-weight: 800; }
    h2 { color: #1976D2; border-bottom: 2px solid #E3F2FD; padding-bottom: 4px; }
    h3 { color: #1976D2; }
    [data-testid="stMetricValue"] { color: #1565C0; font-weight: bold; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# SIDEBAR — Solo lo esencial: API key y modelo
# ═══════════════════════════════════════════════════════════
with st.sidebar:
    # Ícono de hospital
    st.image("https://img.icons8.com/fluency/96/hospital.png", width=72)
    st.title("⚙️ Configuración")
    st.divider()

    # ── API Key ─────────────────────────────────────────────
    st.subheader("🔑 API Key de Gemma")

    # Campo de texto enmascarado para la API key
    # Prellenado con el valor del .env si ya existe
    api_key_input = st.text_input(
        label="Google API Key",
        value=os.getenv("GOOGLE_API_KEY", ""),  # Fallback al .env
        type="password",                          # Muestra asteriscos
        placeholder="AIza...",
        help="Obtén tu clave gratis: https://aistudio.google.com/app/apikey",
    )

    # Si el usuario escribió una key en la UI, la aplicamos al entorno en memoria
    # Esto NO modifica el archivo .env en disco; solo dura esta sesión
    if api_key_input:
        os.environ["GOOGLE_API_KEY"] = api_key_input

    # Indicador visual del estado
    api_key_ok = bool(api_key_input and api_key_input != "pon_tu_api_key_aqui")
    if api_key_ok:
        st.success("✅ API Key lista")
    else:
        st.warning("⚠️ Falta la API Key")
        st.caption("[Obtener clave gratis →](https://aistudio.google.com/app/apikey)")

    st.divider()

    # ── Selector de modelo ──────────────────────────────────
    st.subheader("🤖 Modelo Gemma")

    modelo = st.selectbox(
        label="Modelo",
        options=[
            "gemma-4-26b-a4b-it",   # MoE: rápido, 4B parámetros activos
            "gemma-4-31b-it",        # Dense: más preciso, más lento
        ],
        index=0,
        help="El modelo MoE es más rápido. El Dense 31B es más preciso.",
    )
    # Aplicamos el modelo seleccionado como variable de entorno
    os.environ["GEMMA_MODEL"] = modelo

    st.divider()
    st.caption("Nurse Agent v1.1 · Gemma + OKF + PDF")


# ─────────────────────────────────────────────
# Importamos módulos del agente DESPUÉS de fijar las variables
# de entorno desde la sidebar, para que lean los valores correctos
# ─────────────────────────────────────────────
from agent.okf_converter import OKFConverter    # JSON → OKF/JSON-LD
from agent.pdf_generator import PDFGenerator    # JSON → PDF
from agent.persistence import NurseDatabase     # CRUD SQLite


# ─────────────────────────────────────────────
# Singleton de recursos con caché de Streamlit
# @st.cache_resource crea la instancia UNA sola vez por sesión;
# no se reinicia en cada interacción del usuario con la UI
# ─────────────────────────────────────────────
@st.cache_resource
def get_db():
    """Base de datos SQLite — singleton de sesión."""
    return NurseDatabase()

@st.cache_resource
def get_okf():
    """Convertidor OKF — singleton de sesión."""
    return OKFConverter()

@st.cache_resource
def get_pdf_gen():
    """Generador de PDF — singleton de sesión."""
    return PDFGenerator()


# Obtenemos las instancias cacheadas
db       = get_db()
okf_conv = get_okf()
pdf_gen  = get_pdf_gen()


# ─────────────────────────────────────────────
# Función central que corre el pipeline completo
# Es idéntica para imagen y audio; solo cambia cómo se obtiene la nota
# ─────────────────────────────────────────────
def ejecutar_pipeline(nota: dict, patient_id: str):
    """
    Recibe la nota ya extraída por Gemma (dict) y ejecuta:
      OKF → PDF → SQLite

    Retorna un dict con okf_path, pdf_path y note_id,
    o lanza una excepción si algo falla.
    """
    # Paso 1: Convertir JSON → OKF (JSON-LD semántico)
    st.write("📄 Convirtiendo a OKF (JSON-LD)...")
    okf_path = okf_conv.save(nota, patient_id)

    # Paso 2: Generar el PDF del reporte
    st.write("📑 Generando PDF del reporte...")
    pdf_path = pdf_gen.generate(nota, patient_id)

    # Paso 3: Guardar en SQLite (crea o actualiza el paciente)
    st.write("💾 Guardando en base de datos...")
    db.upsert_patient(patient_id, nota)
    note_id = db.save_note(patient_id, nota, okf_path=okf_path, pdf_path=pdf_path)

    return {"okf_path": okf_path, "pdf_path": pdf_path, "note_id": note_id}


# ─────────────────────────────────────────────
# Función auxiliar para renderizar los resultados
# (reutilizada por la pestaña imagen y la de voz)
# ─────────────────────────────────────────────
def mostrar_resultados(nota: dict, resultado: dict, patient_id: str, modo: str):
    """
    Muestra métricas, JSON, botones de descarga y signos vitales
    después de que el pipeline se completa exitosamente.

    Args:
        nota: Diccionario con los datos extraídos por Gemma
        resultado: Dict con okf_path, pdf_path, note_id
        patient_id: ID del paciente
        modo: "imagen" o "voz" (se muestra en el subtítulo)
    """
    # Métricas de resumen en 3 columnas
    m1, m2, m3 = st.columns(3)
    m1.metric("📋 Nota ID",   f"#{resultado['note_id']}")
    m2.metric("🧑‍⚕️ Paciente", patient_id)
    m3.metric("📅 Fecha",      nota.get("date") or "—")

    st.divider()

    # JSON completo extraído por Gemma (colapsable)
    st.subheader("📋 JSON Extraído por Gemma")
    with st.expander(f"Ver datos estructurados — fuente: {modo}", expanded=True):
        st.json(nota)   # Renderiza con colores, colapso de nodos y búsqueda

    st.divider()

    # Botones de descarga del OKF y el PDF
    st.subheader("⬇️ Descargar archivos")
    btn1, btn2 = st.columns(2)

    with btn1:
        # Leemos el OKF generado y lo ofrecemos como descarga
        okf_text = Path(resultado["okf_path"]).read_text(encoding="utf-8")
        st.download_button(
            label="📄 Descargar OKF (JSON-LD)",
            data=okf_text,
            file_name=f"{patient_id}_nota.jsonld",
            mime="application/ld+json",
            use_container_width=True,
        )

    with btn2:
        # Leemos el PDF como bytes y lo ofrecemos como descarga
        pdf_bytes = Path(resultado["pdf_path"]).read_bytes()
        st.download_button(
            label="📑 Descargar PDF",
            data=pdf_bytes,
            file_name=f"{patient_id}_reporte.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    # Signos vitales como tarjetas métricas (si los hay)
    vitales = nota.get("vital_signs", {})
    if vitales:
        st.divider()
        st.subheader("🩺 Signos Vitales")
        mapeo = {
            "blood_pressure":    ("TA",   "mmHg"),
            "heart_rate":        ("FC",   "lpm"),
            "temperature":       ("Temp", "°C"),
            "oxygen_saturation": ("SpO₂", "%"),
            "respiratory_rate":  ("FR",   "rpm"),
        }
        # Filtramos solo los signos con valor real
        signos_presentes = [(n, u, vitales[c]) for c, (n, u) in mapeo.items() if vitales.get(c) is not None]

        if signos_presentes:
            # Máximo 4 columnas por fila para no quedar apretado
            cols = st.columns(min(len(signos_presentes), 4))
            for i, (nombre, unidad, valor) in enumerate(signos_presentes):
                cols[i % 4].metric(nombre, f"{valor} {unidad}")


# ═══════════════════════════════════════════════════════════
# ENCABEZADO PRINCIPAL
# ═══════════════════════════════════════════════════════════
st.title("🏥 Agente de Notas de Enfermería")
st.caption("Digitaliza notas **escritas a mano** o **dictadas por voz** · Gemma + OKF + PDF · Historial persistente")
st.divider()


# ═══════════════════════════════════════════════════════════
# TABS principales de la aplicación
# ═══════════════════════════════════════════════════════════
tab_imagen, tab_voz, tab_historial, tab_pacientes = st.tabs([
    "📷 Nota por Imagen",   # Sube una foto de la nota manuscrita
    "🎙️ Nota por Voz",      # Graba o sube audio dictando la nota
    "📚 Historial",          # Historial completo de un paciente
    "👥 Pacientes",          # Lista de todos los pacientes
])


# ═══════════════════════════════════════════════════════════
# PESTAÑA 1: NOTA POR IMAGEN
# ═══════════════════════════════════════════════════════════
with tab_imagen:
    col_izq, col_der = st.columns([1, 1], gap="large")

    # ── Columna izquierda: inputs ───────────────────────────
    with col_izq:
        st.subheader("📋 Datos de entrada")

        # ID del paciente
        patient_id_img = st.text_input(
            "ID del Paciente *",
            placeholder="Ej: P001",
            key="pid_imagen",
            help="Identificador único. Agrupa todas las notas del mismo paciente.",
        )

        # Uploader de imagen
        imagen_subida = st.file_uploader(
            "📷 Imagen de la nota manuscrita *",
            type=["jpg", "jpeg", "png", "webp"],
            key="img_uploader",
            help="Foto clara de la nota a mano. Mejor iluminación = mejor resultado.",
        )

        # Preview de la imagen subida
        if imagen_subida:
            st.image(imagen_subida, caption="Vista previa", use_container_width=True)

        st.divider()

        # Validaciones antes de habilitar el botón
        campos_img_ok = bool(patient_id_img.strip()) and imagen_subida is not None

        if not api_key_ok:
            st.error("❌ Configura tu API Key en la barra lateral.")
        elif not campos_img_ok:
            st.info("👆 Completa el ID del paciente y sube una imagen.")

        boton_img = st.button(
            "🚀 Procesar imagen con Gemma",
            type="primary",
            disabled=not (campos_img_ok and api_key_ok),
            use_container_width=True,
            key="btn_imagen",
        )

    # ── Columna derecha: resultados ─────────────────────────
    with col_der:
        st.subheader("📊 Resultados")

        if boton_img and campos_img_ok and api_key_ok:
            # Importamos el agente de visión aquí para que siempre
            # use el GOOGLE_API_KEY más reciente seteado por la sidebar
            from agent.gemma_vision import GemmaVisionAgent

            # Guardamos la imagen en un archivo temporal en disco
            # (Pillow no puede leer de un objeto BytesIO de Streamlit directamente)
            sufijo = "." + imagen_subida.name.split(".")[-1]  # Ej: ".jpg"
            with tempfile.NamedTemporaryFile(suffix=sufijo, delete=False) as tmp:
                tmp.write(imagen_subida.getbuffer())  # Escribimos los bytes
                ruta_tmp = tmp.name                    # Guardamos la ruta temporal

            # st.status muestra una caja de progreso expandible en vivo
            with st.status("⚙️ Procesando imagen...", expanded=True) as estado:
                try:
                    # PASO 1 — Análisis de imagen con Gemma
                    st.write("🤖 Enviando imagen a Gemma...")
                    agente = GemmaVisionAgent()              # Valida API key aquí
                    nota = agente.analyze_image(ruta_tmp)   # Llamada multimodal a la API

                    # Asignamos el patient_id si Gemma no lo detectó en la imagen
                    if not nota.get("patient_id"):
                        nota["patient_id"] = patient_id_img

                    st.write("✅ Datos extraídos correctamente")

                    # PASOS 2-4 — OKF, PDF, SQLite
                    resultado = ejecutar_pipeline(nota, patient_id_img)

                    # Marcamos el estado como completo
                    estado.update(
                        label=f"✅ Nota #{resultado['note_id']} completada",
                        state="complete",
                        expanded=False,
                    )

                    # Mostramos métricas, JSON, botones y signos vitales
                    mostrar_resultados(nota, resultado, patient_id_img, "imagen")

                except ValueError as e:
                    estado.update(label="❌ Error", state="error")
                    st.error(str(e))
                except Exception as e:
                    estado.update(label="❌ Error inesperado", state="error")
                    st.exception(e)  # Muestra el traceback completo
                finally:
                    # Limpiamos el archivo temporal siempre, incluso si hubo error
                    try:
                        os.unlink(ruta_tmp)
                    except Exception:
                        pass


# ═══════════════════════════════════════════════════════════
# PESTAÑA 2: NOTA POR VOZ
# ═══════════════════════════════════════════════════════════
with tab_voz:
    col_voz_izq, col_voz_der = st.columns([1, 1], gap="large")

    # ── Columna izquierda: inputs de voz ────────────────────
    with col_voz_izq:
        st.subheader("🎙️ Dictar nota de voz")
        st.caption(
            "La enfermera puede dictar la nota en voz alta. "
            "Gemma transcribe el audio **y** extrae los datos en un solo paso."
        )

        # ID del paciente para la nota de voz
        patient_id_voz = st.text_input(
            "ID del Paciente *",
            placeholder="Ej: P001",
            key="pid_voz",
            help="Identificador único del paciente.",
        )

        st.divider()

        # ── Opción A: Grabar desde el micrófono ─────────────
        st.markdown("**Opción A — Grabar desde el micrófono**")
        # st.audio_input() graba audio directamente desde el micrófono del navegador
        # Retorna un objeto UploadedFile con los bytes del audio grabado (WAV)
        audio_grabado = st.audio_input(
            label="🔴 Presiona para grabar",
            key="mic_recorder",
            help="Graba la nota de enfermería dictando en voz alta. "
                 "Habla claro e incluye: nombre del paciente, signos vitales, "
                 "medicamentos, observaciones y próximas acciones.",
        )

        st.divider()

        # ── Opción B: Subir archivo de audio ─────────────────
        st.markdown("**Opción B — Subir archivo de audio**")
        # Alternativa para quien ya tiene grabado el audio en un archivo
        audio_subido = st.file_uploader(
            label="📁 Subir archivo de audio",
            type=["wav", "mp3", "ogg", "webm", "m4a"],  # Formatos aceptados por Gemma
            key="audio_uploader",
            help="Formatos soportados: WAV, MP3, OGG, WEBM, M4A",
        )

        # Determinamos cuál fuente de audio usar (grabado tiene prioridad)
        # audio_grabado viene del micrófono; audio_subido viene del uploader
        audio_a_procesar = audio_grabado or audio_subido

        # Si hay audio disponible, lo mostramos como reproductor
        if audio_a_procesar:
            st.audio(audio_a_procesar)  # Reproductor de audio embebido en la UI
            fuente_label = "micrófono" if audio_grabado else "archivo subido"
            st.caption(f"Audio listo — fuente: {fuente_label}")

        st.divider()

        # Validaciones para el botón
        campos_voz_ok = bool(patient_id_voz.strip()) and audio_a_procesar is not None

        if not api_key_ok:
            st.error("❌ Configura tu API Key en la barra lateral.")
        elif not campos_voz_ok:
            st.info("👆 Completa el ID del paciente y graba o sube un audio.")

        boton_voz = st.button(
            "🚀 Procesar voz con Gemini",
            type="primary",
            disabled=not (campos_voz_ok and api_key_ok),
            use_container_width=True,
            key="btn_voz",
        )

        # Guía de dictado para la enfermera
        with st.expander("💡 ¿Cómo dictar la nota?", expanded=False):
            st.markdown("""
**Habla con naturalidad. Ejemplo de dictado:**

> *"Paciente Juan García, ID P001, sala Medicina Interna, cama 5.
> Fecha de hoy, turno de la mañana.
> Signos vitales: tensión arterial 130 sobre 85, frecuencia cardíaca 88,
> temperatura 37.2, saturación de oxígeno 97%.
> El paciente refiere dolor de cabeza y náuseas.
> Se administró Paracetamol 500 miligramos vía oral a las 8 de la mañana.
> Observaciones: paciente estable, refiere mejoría parcial.
> Se realizó cambio de apósito en herida quirúrgica.
> Para el siguiente turno: avisar al médico si la fiebre sube de 38.5."*

Gemma estructura automáticamente toda esa información.
            """)

    # ── Columna derecha: resultados de voz ──────────────────
    with col_voz_der:
        st.subheader("📊 Resultados")

        # 1. Comprobamos que el botón fue presionado y que los requisitos (ID y API Key) están listos
        if boton_voz and campos_voz_ok and api_key_ok:
            from agent.gemma_vision import GemmaVisionAgent

            # 2. Extraemos los bytes puros del objeto UploadedFile que genera Streamlit.
            # Tanto si viene del micrófono como si es un archivo subido, .getvalue() nos da los bytes.
            audio_bytes = audio_a_procesar.getvalue()

            # 3. Determinamos qué tipo MIME (formato) enviarle a Gemini para que sepa cómo leerlo.
            if audio_grabado:
                # El componente st.audio_input() de Streamlit graba en formato WAV por defecto.
                mime_type = "audio/wav"
            else:
                # Si el usuario subió un archivo, deducimos el formato por la extensión del nombre.
                nombre = audio_subido.name.lower()
                mime_map = {
                    ".wav":  "audio/wav",
                    ".mp3":  "audio/mp3",
                    ".ogg":  "audio/ogg",
                    ".webm": "audio/webm",
                    ".m4a":  "audio/mp4",
                }
                # Buscamos en el diccionario. Si no lo encontramos, asumimos wav como salvavidas.
                mime_type = next(
                    (v for k, v in mime_map.items() if nombre.endswith(k)),
                    "audio/wav" 
                )

            # 4. st.status crea una cajita en la interfaz con un spinner de carga y mensajes que van cambiando
            with st.status("⚙️ Procesando audio con Gemini...", expanded=True) as estado:
                try:
                    # PASO 1 — Transcripción y extracción con el SDK de Gemini
                    st.write("🤖 Enviando audio a Gemini (transcripción + extracción)...")
                    agente = GemmaVisionAgent()   # Instanciamos la clase que creamos en agent/gemma_vision.py
                    
                    # Llamamos a nuestro nuevo método, pasándole los bytes y el formato
                    nota = agente.analyze_audio(
                        audio_bytes=audio_bytes,
                        mime_type=mime_type,
                    )

                    # Si el paciente no mencionó su propio ID en el audio, le asignamos
                    # el que la enfermera escribió en la caja de texto.
                    if not nota.get("patient_id"):
                        nota["patient_id"] = patient_id_voz

                    st.write("✅ Nota extraída del audio")

                    # PASOS 2-4 — El pipeline compartido: Convierte a OKF -> Genera PDF -> Guarda en Base de datos (SQLite)
                    resultado = ejecutar_pipeline(nota, patient_id_voz)

                    # 5. Todo salió bien, actualizamos la cajita de estado a verde (complete)
                    estado.update(
                        label=f"✅ Nota #{resultado['note_id']} completada",
                        state="complete",
                        expanded=False,
                    )

                    # 6. Llamamos a nuestra función auxiliar para dibujar las tarjetas con los signos vitales 
                    # y los botones de descarga de PDF.
                    mostrar_resultados(nota, resultado, patient_id_voz, "voz")

                    # 7. Un toque extra para la voz: extraemos el campo "raw_text" que Gemini llenó
                    # y lo mostramos en una caja de texto para que la enfermera pueda leer lo que se entendió.
                    texto_crudo = nota.get("raw_text")
                    if texto_crudo:
                        st.divider()
                        st.subheader("📝 Transcripción del audio")
                        # st.text_area crea un cuadro de texto grande
                        st.text_area(
                            label="Texto detectado por Gemini",
                            value=texto_crudo,
                            height=120,
                            disabled=True,  # Lo bloqueamos para que sea de solo lectura
                        )

                # Manejo de errores controlados (Ej. Gemini responde mal)
                except ValueError as e:
                    estado.update(label="❌ Error", state="error")
                    st.error(str(e))
                # Manejo de cualquier otro error (Fallo de red, error de base de datos)
                except Exception as e:
                    estado.update(label="❌ Error inesperado", state="error")
                    st.exception(e)


# ═══════════════════════════════════════════════════════════
# PESTAÑA 3: HISTORIAL DE UN PACIENTE
# ═══════════════════════════════════════════════════════════
with tab_historial:
    st.subheader("📚 Historial del Paciente")

    buscar_id = st.text_input(
        "ID del Paciente",
        placeholder="Ej: P001",
        key="buscar_hist_id",
    )

    if st.button("🔍 Buscar", key="btn_buscar"):
        if not buscar_id.strip():
            st.warning("Ingresa un ID de paciente.")
        else:
            paciente = db.get_patient(buscar_id.strip())

            if not paciente:
                st.error(f"❌ Paciente '{buscar_id}' no encontrado.")
                st.info("Procesa una imagen o audio del paciente primero.")
            else:
                st.success(f"✅ **{paciente['patient_name']}**")

                # Datos básicos en métricas
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("ID",    paciente["patient_id"])
                c2.metric("Sala",  paciente.get("ward") or "—")
                c3.metric("Cama",  paciente.get("bed") or "—")
                c4.metric("Desde", paciente["created_at"][:10])

                st.divider()

                notas = db.get_patient_notes(buscar_id.strip())
                st.markdown(f"**{len(notas)} nota(s) en el historial:**")

                for i, nota_row in enumerate(notas, 1):
                    nd = nota_row["note_data"]  # Dict con los datos de la nota

                    # Indicador del tipo de entrada (imagen o voz)
                    tipo_input = nd.get("_metadata", {}).get("input_type", "imagen")
                    icono_tipo = "🎙️" if tipo_input == "audio" else "📷"

                    titulo = (
                        f"{icono_tipo} Nota #{nota_row['id']} — "
                        f"{nota_row.get('date') or 'Sin fecha'} "
                        f"{nota_row.get('time') or ''} | "
                        f"Enf: {nota_row.get('nurse') or '—'}"
                    )

                    # Solo la nota más reciente se expande automáticamente
                    with st.expander(titulo, expanded=(i == 1)):
                        h1, h2 = st.columns(2)

                        with h1:
                            # Síntomas
                            sintomas = nd.get("symptoms", [])
                            st.markdown("**🔴 Síntomas:**")
                            for s in sintomas or ["—"]:
                                st.markdown(f"  • {s}")

                            # Intervenciones
                            st.markdown("**⚕️ Intervenciones:**")
                            for iv in (nd.get("interventions") or ["—"]):
                                st.markdown(f"  • {iv}")

                        with h2:
                            # Signos vitales
                            vitales = nd.get("vital_signs", {})
                            if vitales:
                                st.markdown("**🩺 Signos Vitales:**")
                                mapeo_v = {
                                    "blood_pressure": "TA", "heart_rate": "FC",
                                    "temperature": "Temp", "oxygen_saturation": "SpO₂",
                                    "respiratory_rate": "FR",
                                }
                                for campo, nombre in mapeo_v.items():
                                    val = vitales.get(campo)
                                    if val is not None:
                                        st.markdown(f"  **{nombre}:** {val}")

                        # Observaciones en caja azul
                        obs = nd.get("observations")
                        if obs:
                            st.markdown("**📝 Observaciones:**")
                            st.info(obs)

                        # Próximas acciones
                        for act in (nd.get("next_actions") or []):
                            st.markdown(f"  📌 {act}")

                        # Transcripción de audio (si la nota vino de voz)
                        raw = nd.get("raw_text")
                        if raw and tipo_input == "audio":
                            with st.expander("🎙️ Ver transcripción del audio"):
                                st.text(raw)

                        # Botón de descarga del PDF
                        pdf_p = nota_row.get("pdf_path")
                        if pdf_p and Path(pdf_p).exists():
                            st.download_button(
                                label=f"📑 Descargar PDF Nota #{nota_row['id']}",
                                data=Path(pdf_p).read_bytes(),
                                file_name=f"{buscar_id}_nota{nota_row['id']}.pdf",
                                mime="application/pdf",
                                key=f"dl_pdf_{nota_row['id']}",  # key única por botón
                            )


# ═══════════════════════════════════════════════════════════
# PESTAÑA 4: LISTA DE TODOS LOS PACIENTES
# ═══════════════════════════════════════════════════════════
with tab_pacientes:
    st.subheader("👥 Pacientes Registrados")

    if st.button("🔄 Actualizar lista"):
        st.cache_resource.clear()  # Fuerza recarga de la caché

    todos = db.list_patients()

    if not todos:
        st.info(
            "No hay pacientes registrados todavía.\n\n"
            "Procesa una imagen o audio en las pestañas anteriores."
        )
    else:
        col_m1, col_m2 = st.columns(2)
        col_m1.metric("👥 Pacientes", len(todos))
        col_m2.metric("📋 Notas totales", sum(p.get("total_notes", 0) for p in todos))

        st.divider()

        # Tabla interactiva con todos los pacientes
        st.dataframe(
            [
                {
                    "ID":              p["patient_id"],
                    "Nombre":          p["patient_name"],
                    "Sala":            p.get("ward") or "—",
                    "Cama":            p.get("bed") or "—",
                    "Notas":           p.get("total_notes", 0),
                    "Último registro": p["updated_at"][:16].replace("T", " "),
                }
                for p in todos
            ],
            use_container_width=True,
            hide_index=True,
        )
