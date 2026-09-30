# -*- coding: utf-8 -*-
# ==============================================================================
# AGENTE CLÍNICO DE ENFERMERÍA — WORKSTATION DE TRIAGE & MONITOREO UCI
# Estándar Google Cloud OKF v0.2 | Gemini & Gemma Multimodal (Vision & Audio)
# ==============================================================================

import streamlit as st
from pathlib import Path
import os
import json
import tempfile
from datetime import datetime
from dotenv import load_dotenv

def render_html(html_str: str):
    """Renderiza HTML puro eliminando sangrías de cada línea para evitar bloques de código Markdown."""
    clean = " ".join([line.strip() for line in html_str.splitlines() if line.strip()])
    st.markdown(clean, unsafe_allow_html=True)

# Cargar variables de entorno
load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=False)

# Configuración de página de Streamlit
st.set_page_config(
    page_title="Agente Clínico de Enfermería | Triage & UCI",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ------------------------------------------------------------------------------
# INYECCIÓN DE ESTILOS CSS QUIRÚRGICOS (Dark Clinical Obsidian & Medical Teal)
# ------------------------------------------------------------------------------
render_html("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&family=Caveat:wght@600;700&display=swap');

    :root {
        --bg-main: #070d0b;
        --bg-card: #0c1512;
        --bg-card-sub: #101c18;
        --border-card: #182823;
        --border-subtle: #243e37;
        --teal-main: #00d2aa;
        --teal-light: #34d399;
        --cyan-telemetry: #38bdf8;
        --emerald-vitals: #10b981;
        --coral-alert: #f87171;
        --amber-warning: #fbbf24;
        --text-pure: #f8fafc;
        --text-subtle: #94a3b8;
        --text-dim: #64748b;
    }

    #MainMenu, header, footer { visibility: hidden !important; }
    
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        padding-left: 1.8rem !important;
        padding-right: 1.8rem !important;
        max-width: 100% !important;
    }

    body, html, [data-testid="stAppViewContainer"] {
        background-color: var(--bg-main) !important;
        color: var(--text-pure) !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    /* BARRA SUPERIOR DE NAVEGACIÓN CLÍNICA */
    .clinical-navbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: linear-gradient(180deg, #0d1b17 0%, #08120e 100%);
        border: 1px solid var(--border-card);
        border-radius: 14px;
        padding: 12px 24px;
        margin-bottom: 18px;
        box-shadow: 0 6px 24px rgba(0, 0, 0, 0.45);
    }
    .brand-section {
        display: flex;
        align-items: center;
        gap: 14px;
    }
    .brand-icon-box {
        width: 40px;
        height: 40px;
        border-radius: 10px;
        background: linear-gradient(135deg, rgba(0, 210, 170, 0.22) 0%, rgba(16, 185, 129, 0.12) 100%);
        border: 1px solid rgba(0, 210, 170, 0.4);
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 0 16px rgba(0, 210, 170, 0.3);
    }
    .brand-title {
        font-size: 1.35rem;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: -0.02em;
        margin: 0;
    }
    .brand-subtitle {
        font-size: 0.95rem;
        font-weight: 400;
        color: var(--text-subtle);
        margin: 0;
        margin-left: 10px;
        border-left: 1px solid var(--border-subtle);
        padding-left: 12px;
    }
    .nav-right-section {
        display: flex;
        align-items: center;
        gap: 18px;
    }
    .notification-bell {
        position: relative;
        cursor: pointer;
        padding: 8px;
        border-radius: 50%;
        background: rgba(16, 28, 24, 0.6);
        border: 1px solid var(--border-card);
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .bell-dot {
        position: absolute;
        top: 6px;
        right: 6px;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: var(--coral-alert);
        border: 2px solid var(--bg-card);
    }
    .nurse-badge {
        display: flex;
        align-items: center;
        gap: 12px;
        background: rgba(16, 28, 24, 0.75);
        border: 1px solid var(--border-card);
        padding: 6px 16px;
        border-radius: 30px;
    }
    .nurse-avatar {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        background: linear-gradient(135deg, #00d2aa, #059669);
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        color: #070d0b;
        font-size: 0.9rem;
        box-shadow: 0 0 12px rgba(0, 210, 170, 0.4);
    }
    .nurse-info {
        display: flex;
        flex-direction: column;
    }
    .nurse-name {
        font-size: 0.88rem;
        font-weight: 700;
        color: #ffffff;
    }
    .nurse-id {
        font-size: 0.74rem;
        color: var(--teal-main);
        font-family: 'JetBrains Mono', monospace;
    }

    /* TARJETAS CLÍNICAS MODULARES */
    .clinical-card {
        background-color: var(--bg-card);
        border: 1px solid var(--border-card);
        border-radius: 14px;
        padding: 18px 20px;
        margin-bottom: 16px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
        transition: border-color 0.25s ease, box-shadow 0.25s ease;
    }
    .clinical-card:hover {
        border-color: var(--border-subtle);
        box-shadow: 0 6px 24px rgba(0, 210, 170, 0.05);
    }
    .card-header-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 14px;
        padding-bottom: 10px;
        border-bottom: 1px solid var(--border-card);
    }
    .card-title {
        font-size: 1.02rem;
        font-weight: 700;
        color: #f1f5f9;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .card-action-dots {
        color: var(--text-dim);
        font-size: 1.1rem;
        cursor: pointer;
    }

    /* MONITOR TELEMETRÍA UCI */
    .vitals-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 12px;
    }
    .vital-tile {
        background: var(--bg-card-sub);
        border: 1px solid var(--border-card);
        border-radius: 10px;
        padding: 12px 14px;
        position: relative;
    }
    .vital-tile-wide {
        grid-column: span 2;
    }
    .vital-label {
        font-size: 0.74rem;
        font-weight: 600;
        color: var(--text-subtle);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 4px;
    }
    .vital-value-box {
        display: flex;
        align-items: baseline;
        gap: 6px;
        margin-bottom: 6px;
    }
    .vital-val {
        font-size: 1.85rem;
        font-weight: 800;
        color: #ffffff;
        line-height: 1;
        letter-spacing: -0.02em;
    }
    .vital-unit {
        font-size: 0.82rem;
        color: var(--teal-main);
        font-weight: 600;
    }
    .vital-badge-status {
        position: absolute;
        top: 12px;
        right: 12px;
        font-size: 0.7rem;
        font-weight: 600;
        padding: 2px 7px;
        border-radius: 10px;
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }

    /* ONDAS SVG CON ANIMACIÓN DE PULSO */
    .ecg-line {
        filter: drop-shadow(0 0 5px rgba(0, 210, 170, 0.55));
    }
    .bp-line {
        filter: drop-shadow(0 0 5px rgba(56, 189, 248, 0.45));
    }
    .spo2-line {
        filter: drop-shadow(0 0 4px rgba(16, 185, 129, 0.5));
    }

    /* TRIAGE Y RESUMEN */
    .triage-section-title {
        font-size: 0.8rem;
        font-weight: 700;
        color: var(--text-subtle);
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-top: 10px;
        margin-bottom: 6px;
    }
    .symptom-tag {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 0.84rem;
        color: #e2e8f0;
        margin-bottom: 6px;
    }
    .symptom-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background-color: var(--teal-main);
        display: inline-block;
        flex-shrink: 0;
    }
    .allergy-badge {
        display: inline-block;
        font-size: 0.75rem;
        font-weight: 600;
        color: #fca5a5;
        background: rgba(239, 68, 68, 0.12);
        border: 1px solid rgba(239, 68, 68, 0.35);
        padding: 3px 8px;
        border-radius: 6px;
        margin-right: 6px;
        margin-bottom: 6px;
    }
    .status-badge-live {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 0.82rem;
        font-weight: 700;
        color: #34d399;
        background: rgba(16, 185, 129, 0.15);
        border: 1px solid rgba(16, 185, 129, 0.35);
        padding: 4px 10px;
        border-radius: 8px;
    }

    /* JSON-LD TERMINAL (Google Cloud OKF) */
    .okf-terminal {
        background: #050a08;
        border: 1px solid #142420;
        border-radius: 10px;
        padding: 14px 16px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.77rem;
        color: #e2e8f0;
        line-height: 1.6;
        max-height: 380px;
        overflow-y: auto;
    }
    .code-line {
        display: flex;
    }
    .line-no {
        width: 26px;
        color: #475569;
        user-select: none;
        text-align: right;
        margin-right: 12px;
    }
    .k-tag { color: #38bdf8; font-weight: 600; }
    .s-tag { color: #34d399; }
    .n-tag { color: #fbbf24; }
    .p-tag { color: #64748b; }

    /* PRESCRIPCIÓN CLÁSICA RX VS DIGITAL */
    .rx-card-container {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
    }
    .rx-paper-slip {
        background: #fdfbf7;
        color: #1e293b;
        border-radius: 10px;
        padding: 16px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.4);
        border: 1px solid #e2e8f0;
    }
    .rx-header-text {
        font-size: 0.78rem;
        font-weight: 700;
        color: #334155;
        border-bottom: 2px solid #cbd5e1;
        padding-bottom: 6px;
        margin-bottom: 10px;
    }
    .rx-dr-title {
        font-size: 0.88rem;
        font-weight: 800;
        color: #0f172a;
    }
    .rx-handwriting {
        font-family: 'Caveat', cursive, sans-serif;
        font-size: 1.18rem;
        line-height: 1.35;
        color: #1e293b;
    }
    .rx-digital-card {
        background: var(--bg-card-sub);
        border: 1px solid var(--border-card);
        border-radius: 10px;
        padding: 14px;
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    .rx-digital-item {
        background: rgba(7, 13, 11, 0.7);
        border: 1px solid #182823;
        border-radius: 6px;
        padding: 7px 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .rx-med-name {
        font-size: 0.8rem;
        font-weight: 600;
        color: #ffffff;
    }
    .rx-med-dose {
        font-size: 0.72rem;
        color: var(--teal-main);
        font-family: 'JetBrains Mono', monospace;
    }

    /* INFORME MÉDICO PDF LIVE PREVIEW */
    .pdf-preview-sheet {
        background: #ffffff;
        color: #0f172a;
        border-radius: 10px;
        padding: 22px;
        font-size: 0.76rem;
        line-height: 1.45;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        border: 1px solid #cbd5e1;
        max-height: 520px;
        overflow-y: auto;
    }
    .pdf-clinic-logo {
        display: flex;
        align-items: center;
        justify-content: space-between;
        border-bottom: 2px solid #00d2aa;
        padding-bottom: 8px;
        margin-bottom: 14px;
    }
    .pdf-doc-title {
        font-size: 0.95rem;
        font-weight: 800;
        color: #0f172a;
        text-transform: uppercase;
        letter-spacing: -0.01em;
        margin: 0;
    }
    .pdf-meta-box {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 8px 12px;
        margin-bottom: 12px;
    }
    .pdf-table {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 12px;
        font-size: 0.72rem;
    }
    .pdf-table th {
        background: #f1f5f9;
        text-align: left;
        padding: 5px 8px;
        border: 1px solid #cbd5e1;
        color: #334155;
    }
    .pdf-table td {
        padding: 5px 8px;
        border: 1px solid #e2e8f0;
        color: #1e293b;
    }

    /* BOTONES PRIMARIOS Y DESCARGAS */
    div[data-testid="stButton"] > button {
        background: linear-gradient(135deg, #00d2aa 0%, #059669 100%) !important;
        color: #070d0b !important;
        font-weight: 700 !important;
        font-size: 0.88rem !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 20px !important;
        box-shadow: 0 4px 14px rgba(0, 210, 170, 0.28) !important;
        transition: all 0.2s ease !important;
        width: 100% !important;
    }
    div[data-testid="stButton"] > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(0, 210, 170, 0.45) !important;
    }

    div[data-testid="stDownloadButton"] > button {
        background: linear-gradient(135deg, #00d2aa 0%, #059669 100%) !important;
        color: #070d0b !important;
        font-weight: 700 !important;
        font-size: 0.88rem !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 20px !important;
        box-shadow: 0 4px 14px rgba(0, 210, 170, 0.28) !important;
        transition: all 0.2s ease !important;
        width: 100% !important;
    }
    div[data-testid="stDownloadButton"] > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(0, 210, 170, 0.45) !important;
    }

    /* ESTILO DE TABS */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: var(--bg-card);
        padding: 6px;
        border-radius: 12px;
        border: 1px solid var(--border-card);
        margin-bottom: 18px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important;
        border-radius: 8px !important;
        color: var(--text-subtle) !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        padding: 8px 18px !important;
        border: none !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(0, 210, 170, 0.15) !important;
        color: var(--teal-main) !important;
        border: 1px solid rgba(0, 210, 170, 0.35) !important;
    }
</style>
""")

# ------------------------------------------------------------------------------
# MÓDULOS DEL AGENTE (SINGLETONS CON CACHÉ)
# ------------------------------------------------------------------------------
from agent.okf_converter import OKFConverter
from agent.pdf_generator import PDFGenerator
from agent.persistence import NurseDatabase

@st.cache_resource
def get_db():
    return NurseDatabase()

@st.cache_resource
def get_okf():
    return OKFConverter()

@st.cache_resource
def get_pdf_gen():
    return PDFGenerator()

db = get_db()
okf_conv = get_okf()
pdf_gen = get_pdf_gen()

# ------------------------------------------------------------------------------
# CASO DEMO CLÍNICO DE REFERENCIA ("Juan Pérez - UCI")
# ------------------------------------------------------------------------------
DEMO_CASE = {
    "patient_name": "Juan Pérez",
    "patient_id": "P-186602023",
    "cedula": "1048291024",
    "date": datetime.now().strftime("%d %b %Y"),
    "time": "14:30",
    "ward": "Unidad de Cuidados Intensivos (UCI)",
    "bed": "Cama 04",
    "nurse": "Elena Ramírez (ID: 7412)",
    "physician": "Dr. Carlos García (Reg: 45892-MED)",
    "vital_signs": {
        "heart_rate": 88,
        "blood_pressure": "128/84 mmHg",
        "oxygen_saturation": "97%",
        "respiratory_rate": 18,
        "temperature": "37.1 °C"
    },
    "symptoms": [
        "Dolor de Pecho opresivo retroesternal (EVA 6/10)",
        "Disnea de medianos esfuerzos",
        "Tos seca no productiva (48h de evolución)"
    ],
    "allergies": [
        "Alergia severa a Penicilina (Anafilaxia previa)",
        "Intolerancia gástrica a AINES"
    ],
    "history": [
        "Cardiopatía isquémica diagnosticada en 2023",
        "Hipertensión arterial esencial estadio II",
        "Dislipidemia mixta en tratamiento"
    ],
    "status": "Estable bajo monitorización hemodinámica continua",
    "interventions": [
        "Monitorización ECG y oximetría continua en UCI",
        "Oxigenoterapia por cánula nasal a 2 L/min",
        "Canalización de vía venosa periférica permeable en MSD",
        "Electrocardiograma seriado de 12 derivaciones"
    ],
    "prescriptions": [
        {"med": "Aspirina (Ácido Acetilsalicílico)", "dose": "100 mg", "route": "VO", "freq": "Cada 24 horas", "status": "Administrado"},
        {"med": "Atorvastatina", "dose": "40 mg", "route": "VO", "freq": "Cada noche", "status": "Administrado"},
        {"med": "Enoxaparina Sódica", "dose": "60 mg / 0.6 ml", "route": "SC", "freq": "Cada 12 horas", "status": "Programado 20:00"},
        {"med": "Omeprazol", "dose": "20 mg", "route": "VO", "freq": "Cada 24 horas en ayunas", "status": "Administrado"},
        {"med": "Metoprolol Tartrato", "dose": "25 mg", "route": "VO", "freq": "Cada 12 horas", "status": "Administrado"}
    ],
    "observations": "Paciente lúcido, afebril, hemodinámicamente estable. Refiere disminución progresiva del dolor torácico post-analgesia. Ruidos cardíacos rítmicos, murmullo vesicular conservado sin ruidos agregados. Buena perfusión capilar distal (<2s).",
    "next_actions": [
        "Control seriado de Troponina I a las 6 horas",
        "Monitoreo horario de presión arterial y ritmo cardíaco",
        "Vigilar signos de sangrado por anticoagulación"
    ]
}

# Inicialización del caso activo en sesión
if "active_case" not in st.session_state:
    st.session_state["active_case"] = DEMO_CASE

# ------------------------------------------------------------------------------
# SIDEBAR — CONFIGURACIÓN TÉCNICA Y API KEY
# ------------------------------------------------------------------------------
with st.sidebar:
    render_html("""
    <div style="text-align: center; padding: 10px 0;">
        <div style="font-size: 2.2rem; margin-bottom: 4px;">🏥</div>
        <div style="font-weight: 800; font-size: 1.1rem; color: #ffffff;">Estación UCI</div>
        <div style="font-size: 0.76rem; color: #00d2aa;">Google Cloud OKF v0.2</div>
    </div>
    """)
    st.divider()

    st.subheader("🔑 Google API Key")
    api_key_input = st.text_input(
        label="Clave de API",
        value=os.getenv("GOOGLE_API_KEY", ""),
        type="password",
        placeholder="AIzaSy...",
        help="Obtén tu API key gratuita en Google AI Studio: https://aistudio.google.com/app/apikey"
    )
    if api_key_input:
        os.environ["GOOGLE_API_KEY"] = api_key_input

    api_key_ok = bool(api_key_input and api_key_input != "pon_tu_api_key_aqui")
    if api_key_ok:
        st.success("● API Key Activa")
    else:
        st.warning("⚠️ Sin API Key (Demo activa)")

    st.divider()
    st.subheader("🤖 Modelo de IA")
    modelo = st.selectbox(
        label="Motor LLM / VLM",
        options=[
            "gemini-2.5-flash",
            "gemma-4-26b-a4b-it",
            "gemma-4-31b-it",
        ],
        index=0,
    )
    os.environ["GEMMA_MODEL"] = modelo

    st.divider()
    render_html("""
    <div style="font-size: 0.75rem; color: #64748b; line-height: 1.5;">
        <b>Enfermera a Cargo:</b> Elena Ramírez<br>
        <b>ID Personal:</b> 7412<br>
        <b>Servicio:</b> Cuidados Intensivos (UCI)<br>
        <b>Estándar:</b> OKF / JSON-LD / FHIR
    </div>
    """)

# ------------------------------------------------------------------------------
# HEADER CLÍNICO PRINCIPAL
# ------------------------------------------------------------------------------
render_html("""
<div class="clinical-navbar">
    <div class="brand-section">
        <div class="brand-icon-box">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 14h-2v-3H8v-2h3V8h2v3h3v2h-3v3z" fill="#00d2aa"/>
            </svg>
        </div>
        <div style="display: flex; align-items: baseline;">
            <h1 class="brand-title">Agente Clínico de Enfermería</h1>
            <span class="brand-subtitle">Triage & Registros Clínicos</span>
        </div>
    </div>
    <div class="nav-right-section">
        <div class="notification-bell" title="Alertas de Triage (1 activa)">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
                <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
            </svg>
            <div class="bell-dot"></div>
        </div>
        <div class="nurse-badge">
            <div class="nurse-avatar">ER</div>
            <div class="nurse-info">
                <span class="nurse-name">Elena Ramirez</span>
                <span class="nurse-id">ID: 7412 · UCI</span>
            </div>
            <span style="color: #64748b; font-size: 0.75rem;">▼</span>
        </div>
    </div>
</div>
""")

# ------------------------------------------------------------------------------
# PESTAÑAS PRINCIPALES DE OPERACIÓN
# ------------------------------------------------------------------------------
tab_dash, tab_img, tab_voz, tab_hist, tab_pacs = st.tabs([
    "🩺 Dashboard Clínico & Triage",
    "📷 Nota por Imagen (Gemma Vision)",
    "🎙️ Nota por Voz (Gemini Audio)",
    "📋 Historial de Paciente",
    "👥 Directorio de Pacientes"
])

# ------------------------------------------------------------------------------
# PESTAÑA 1: DASHBOARD CLÍNICO & TRIAGE (REPLICA EXACTA DE LA IMAGEN)
# ------------------------------------------------------------------------------
with tab_dash:
    # Barra de acciones rápidas
    top_c1, top_c2 = st.columns([3, 1])
    with top_c1:
        render_html(f"""
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
            <span style="font-size: 0.85rem; color: #94a3b8; font-weight: 600;">CASO ACTIVO:</span>
            <span style="font-size: 0.95rem; color: #ffffff; font-weight: 700; background: #101c18; border: 1px solid #182823; padding: 4px 12px; border-radius: 8px;">
                👤 {st.session_state['active_case']['patient_name']} ({st.session_state['active_case']['patient_id']}) — {st.session_state['active_case']['ward']} ({st.session_state['active_case']['bed']})
            </span>
            <span class="status-badge-live" style="background: rgba(239,68,68,0.15); color: #f87171; border: 1px solid rgba(239,68,68,0.35);">● Nivel II: Urgente Prioritario</span>
        </div>
        """)
    with top_c2:
        if st.button("⚡ Cargar Caso Clínico Demo (Juan Pérez - UCI)", key="btn_load_demo"):
            st.session_state["active_case"] = DEMO_CASE
            st.rerun()

    # Layout de 3 columnas (Izquierda: Telemetría + JSON, Centro: Triage + Rx, Derecha: PDF Report)
    col_telemetria, col_triage, col_pdf = st.columns([1.15, 1.05, 1.0], gap="medium")

    # ==================== COLUMNA 1: TELEMETRÍA UCI & JSON-LD ====================
    with col_telemetria:
        # TARJETA 1: MONITOR DE SIGNOS VITALES
        render_html(f"""
        <div class="clinical-card">
            <div class="card-header-row">
                <h3 class="card-title">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#00d2aa" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>
                    Monitor de Signos Vitales (Paciente: {st.session_state['active_case']['patient_name']})
                </h3>
                <span class="card-action-dots">•••</span>
            </div>
            <div class="vitals-grid">
                <div class="vital-tile">
                    <div class="vital-label">Frecuencia Cardíaca</div>
                    <div class="vital-value-box">
                        <span class="vital-val">{st.session_state['active_case']['vital_signs']['heart_rate']}</span>
                        <span class="vital-unit">lpm</span>
                    </div>
                    <svg viewBox="0 0 220 50" class="telemetry-wave">
                        <path class="ecg-line" d="M 0 30 L 30 30 L 35 28 L 40 32 L 45 30 L 60 30 L 65 33 L 70 8 L 76 45 L 82 25 L 87 31 L 93 30 L 120 30 L 125 28 L 130 32 L 135 30 L 150 30 L 155 33 L 160 8 L 166 45 L 172 25 L 177 31 L 183 30 L 220 30" fill="none" stroke="#00d2aa" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    <div style="font-size: 0.68rem; color: #64748b; margin-top: 2px;">Límite: 60 - 100</div>
                </div>
                <div class="vital-tile">
                    <span class="vital-badge-status">● Límites</span>
                    <div class="vital-label">Presión Arterial</div>
                    <div class="vital-value-box">
                        <span class="vital-val">{st.session_state['active_case']['vital_signs']['blood_pressure'].split(' ')[0]}</span>
                        <span class="vital-unit">mmHg</span>
                    </div>
                    <svg viewBox="0 0 220 50" class="telemetry-wave">
                        <path class="bp-line" d="M 0 38 Q 18 12, 35 18 T 70 38 Q 88 12, 105 18 T 140 38 Q 158 12, 175 18 T 210 38 L 220 38" fill="none" stroke="#38bdf8" stroke-width="2.2" stroke-linecap="round"/>
                    </svg>
                    <div style="font-size: 0.68rem; color: #64748b; margin-top: 2px;">Normal: &lt; 130/85</div>
                </div>
                <div class="vital-tile">
                    <div class="vital-label">Saturación O2</div>
                    <div class="vital-value-box">
                        <span class="vital-val">{st.session_state['active_case']['vital_signs']['oxygen_saturation']}</span>
                    </div>
                    <svg viewBox="0 0 220 50" class="telemetry-wave">
                        <defs>
                            <linearGradient id="o2Grad" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="0%" stop-color="#00d2aa" stop-opacity="0.45"/>
                                <stop offset="100%" stop-color="#00d2aa" stop-opacity="0.0"/>
                            </linearGradient>
                        </defs>
                        <path d="M 0 36 Q 20 16, 38 20 T 75 36 Q 95 16, 113 20 T 150 36 Q 170 16, 188 20 T 220 36 L 220 50 L 0 50 Z" fill="url(#o2Grad)"/>
                        <path class="spo2-line" d="M 0 36 Q 20 16, 38 20 T 75 36 Q 95 16, 113 20 T 150 36 Q 170 16, 188 20 T 220 36" fill="none" stroke="#00d2aa" stroke-width="2"/>
                    </svg>
                    <div style="display: flex; justify-content: space-between; font-size: 0.68rem; color: #64748b; margin-top: 2px;">
                        <span>Meta &gt; 95%</span>
                        <span>O2 Cánula 2L</span>
                    </div>
                </div>
                <div class="vital-tile">
                    <div class="vital-label">Frecuencia Respiratoria</div>
                    <div class="vital-value-box">
                        <span class="vital-val">{st.session_state['active_case']['vital_signs']['respiratory_rate']}</span>
                        <span class="vital-unit">rpm</span>
                    </div>
                    <svg viewBox="0 0 220 50" class="telemetry-wave">
                        <path d="M 0 28 C 22 10, 44 10, 66 28 C 88 46, 110 46, 132 28 C 154 10, 176 10, 198 28 L 220 28" fill="none" stroke="#38bdf8" stroke-width="2" stroke-linecap="round"/>
                    </svg>
                    <div style="font-size: 0.68rem; color: #64748b; margin-top: 2px;">Rango: 12 - 20 rpm</div>
                </div>
                <div class="vital-tile vital-tile-wide">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div class="vital-label">Temperatura Axilar</div>
                            <div class="vital-value-box" style="margin-bottom: 0;">
                                <span class="vital-val">{st.session_state['active_case']['vital_signs']['temperature']}</span>
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <span class="status-badge-live">● Afebril / Estable</span>
                            <div style="font-size: 0.7rem; color: #64748b; margin-top: 4px;">Última medición: hace 15 min</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """)

        # TARJETA 4: EXTRACCIÓN DE DATOS CLÍNICOS (JSON-LD)
        render_html(f"""
        <div class="clinical-card">
            <div class="card-header-row">
                <h3 class="card-title">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="2"><polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline></svg>
                    Extracción de Datos Clínicos (JSON-LD)
                </h3>
                <span class="card-action-dots">•••</span>
            </div>
            <div class="okf-terminal">
                <div class="code-line"><span class="line-no">1</span><span class="p-tag">&#123;</span></div>
                <div class="code-line"><span class="line-no">2</span>&nbsp;&nbsp;<span class="k-tag">"@context"</span><span class="p-tag">:</span>&nbsp;<span class="s-tag">"https://schema.org"</span><span class="p-tag">,</span></div>
                <div class="code-line"><span class="line-no">3</span>&nbsp;&nbsp;<span class="k-tag">"@type"</span><span class="p-tag">:</span>&nbsp;<span class="s-tag">"MedicalRecord"</span><span class="p-tag">,</span></div>
                <div class="code-line"><span class="line-no">4</span>&nbsp;&nbsp;<span class="k-tag">"patientId"</span><span class="p-tag">:</span>&nbsp;<span class="s-tag">"{st.session_state['active_case']['patient_id']}"</span><span class="p-tag">,</span></div>
                <div class="code-line"><span class="line-no">5</span>&nbsp;&nbsp;<span class="k-tag">"vitals"</span><span class="p-tag">:</span>&nbsp;<span class="p-tag">&#123;</span></div>
                <div class="code-line"><span class="line-no">6</span>&nbsp;&nbsp;&nbsp;&nbsp;<span class="k-tag">"heartRate"</span><span class="p-tag">:</span>&nbsp;<span class="n-tag">{st.session_state['active_case']['vital_signs']['heart_rate']}</span><span class="p-tag">,</span></div>
                <div class="code-line"><span class="line-no">7</span>&nbsp;&nbsp;&nbsp;&nbsp;<span class="k-tag">"bloodPressure"</span><span class="p-tag">:</span>&nbsp;<span class="s-tag">"{st.session_state['active_case']['vital_signs']['blood_pressure']}"</span><span class="p-tag">,</span></div>
                <div class="code-line"><span class="line-no">8</span>&nbsp;&nbsp;&nbsp;&nbsp;<span class="k-tag">"oxygenSaturation"</span><span class="p-tag">:</span>&nbsp;<span class="s-tag">"{st.session_state['active_case']['vital_signs']['oxygen_saturation']}"</span><span class="p-tag">,</span></div>
                <div class="code-line"><span class="line-no">9</span>&nbsp;&nbsp;&nbsp;&nbsp;<span class="k-tag">"temperature"</span><span class="p-tag">:</span>&nbsp;<span class="s-tag">"{st.session_state['active_case']['vital_signs']['temperature']}"</span></div>
                <div class="code-line"><span class="line-no">10</span>&nbsp;&nbsp;<span class="p-tag">&#125;,</span></div>
                <div class="code-line"><span class="line-no">11</span>&nbsp;&nbsp;<span class="k-tag">"conditions"</span><span class="p-tag">:</span>&nbsp;<span class="p-tag">[</span></div>
                <div class="code-line"><span class="line-no">12</span>&nbsp;&nbsp;&nbsp;&nbsp;<span class="p-tag">&#123;</span></div>
                <div class="code-line"><span class="line-no">13</span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span class="k-tag">"@type"</span><span class="p-tag">:</span>&nbsp;<span class="s-tag">"MedicalCondition"</span><span class="p-tag">,</span></div>
                <div class="code-line"><span class="line-no">14</span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span class="k-tag">"name"</span><span class="p-tag">:</span>&nbsp;<span class="s-tag">"{st.session_state['active_case']['symptoms'][0]}"</span><span class="p-tag">,</span></div>
                <div class="code-line"><span class="line-no">15</span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span class="k-tag">"status"</span><span class="p-tag">:</span>&nbsp;<span class="s-tag">"En observación activa"</span></div>
                <div class="code-line"><span class="line-no">16</span>&nbsp;&nbsp;&nbsp;&nbsp;<span class="p-tag">&#125;</span></div>
                <div class="code-line"><span class="line-no">17</span>&nbsp;&nbsp;<span class="p-tag">],</span></div>
                <div class="code-line"><span class="line-no">18</span>&nbsp;&nbsp;<span class="k-tag">"procedures"</span><span class="p-tag">:</span>&nbsp;<span class="p-tag">[</span></div>
                <div class="code-line"><span class="line-no">19</span>&nbsp;&nbsp;&nbsp;&nbsp;<span class="s-tag">"Monitorización hemodinámica continua"</span><span class="p-tag">,</span></div>
                <div class="code-line"><span class="line-no">20</span>&nbsp;&nbsp;&nbsp;&nbsp;<span class="s-tag">"Oxigenoterapia cánula nasal 2L"</span></div>
                <div class="code-line"><span class="line-no">21</span>&nbsp;&nbsp;<span class="p-tag">]</span></div>
                <div class="code-line"><span class="line-no">22</span><span class="p-tag">&#125;</span></div>
            </div>
        </div>
        """)

    # ==================== COLUMNA 2: TRIAGE & PRESCRIPCIÓN ====================
    with col_triage:
        # TARJETA 2: TRIAGE Y RESUMEN DEL PACIENTE
        sintomas_html = "".join([f'<div class="symptom-tag"><span class="symptom-dot"></span>{s}</div>' for s in st.session_state['active_case']['symptoms']])
        alergias_html = "".join([f'<span class="allergy-badge">⚠️ {a}</span>' for a in st.session_state['active_case']['allergies']])
        antecedentes_html = "".join([f'<div style="font-size: 0.8rem; color: #cbd5e1; margin-bottom: 4px;">• {h}</div>' for h in st.session_state['active_case']['history']])

        render_html(f"""
        <div class="clinical-card">
            <div class="card-header-row">
                <h3 class="card-title">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                    Triage y Resumen del Paciente ({st.session_state['active_case']['patient_name']})
                </h3>
                <span class="card-action-dots">•••</span>
            </div>
            <div class="triage-section-title">Síntomas Reportados</div>
            <div style="margin-bottom: 10px;">
                {sintomas_html}
            </div>
            <div class="triage-section-title">Alergias Conocidas</div>
            <div style="margin-bottom: 10px;">
                {alergias_html}
            </div>
            <div class="triage-section-title">Antecedentes Clínicos</div>
            <div style="margin-bottom: 12px;">
                {antecedentes_html}
            </div>
            <div class="triage-section-title">Estado Actual</div>
            <div style="margin-top: 4px;">
                <span class="status-badge-live">● {st.session_state['active_case']['status']}</span>
            </div>
        </div>
        """)

        # TARJETA 5: PRESCRIPCIÓN MÉDICA (DIGITALIZADA)
        digital_rx_html = "".join([
            f'<div class="rx-digital-item">'
            f'  <div><div class="rx-med-name">{p["med"]}</div><div style="font-size: 0.7rem; color: #94a3b8;">{p["route"]} · {p["freq"]}</div></div>'
            f'  <div style="text-align: right;"><span class="rx-med-dose">{p["dose"]}</span><div style="font-size: 0.68rem; color: #34d399;">✓ {p["status"]}</div></div>'
            f'</div>'
            for p in st.session_state['active_case']['prescriptions']
        ])

        render_html(f"""
        <div class="clinical-card">
            <div class="card-header-row">
                <h3 class="card-title">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path></svg>
                    Prescripción Médica (Digitalizada)
                </h3>
                <span class="card-action-dots">•••</span>
            </div>
            <div class="rx-card-container">
                <div class="rx-paper-slip">
                    <div class="rx-header-text">
                        <div class="rx-dr-title">Dr. Carlos García</div>
                        <div style="font-size: 0.68rem; color: #64748b;">Especialista Medicina Interna · 28 Oct 2026</div>
                    </div>
                    <div style="font-size: 1.3rem; font-weight: 800; font-family: serif; color: #0f172a; margin-bottom: 4px;">℞ Prescripción</div>
                    <div class="rx-handwriting">
                        1. Aspirina 100mg<br>
                        2. Atorvastatina 40mg<br>
                        3. Enoxaparina 60mg<br>
                        4. Omeprazol 20mg<br>
                        5. Metoprolol 25mg
                    </div>
                    <div style="text-align: right; margin-top: 10px; font-family: 'Caveat', cursive; font-size: 1.1rem; color: #334155; border-top: 1px dashed #cbd5e1; padding-top: 4px;">
                        Dr. García
                    </div>
                </div>
                <div class="rx-digital-card">
                    <div style="font-size: 0.74rem; font-weight: 700; color: #94a3b8; text-transform: uppercase;">Transcripción Verificada</div>
                    {digital_rx_html}
                </div>
            </div>
        </div>
        """)

    # ==================== COLUMNA 3: GENERADOR DE INFORMES PDF ====================
    with col_pdf:
        # TARJETA 3: GENERADOR DE INFORMES MÉDICOS (PDF)
        render_html(f"""
        <div class="clinical-card">
            <div class="card-header-row">
                <h3 class="card-title">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#00d2aa" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                    Generador de Informes Médicos (PDF)
                </h3>
                <span class="status-badge-live">● Live Preview</span>
            </div>
            <div class="pdf-preview-sheet">
                <div class="pdf-clinic-logo">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <svg width="22" height="22" viewBox="0 0 24 24" fill="none"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 14h-2v-3H8v-2h3V8h2v3h3v2h-3v3z" fill="#00d2aa"/></svg>
                        <span style="font-weight: 800; font-size: 0.85rem; color: #0f172a;">HOSPITAL CLÍNICO METROPOLITANO</span>
                    </div>
                    <span style="font-size: 0.68rem; color: #64748b;">{st.session_state['active_case']['date']} · {st.session_state['active_case']['time']}</span>
                </div>
                <div class="pdf-doc-title">INFORME DE TRIAGE Y EVALUACIÓN CLÍNICA</div>
                <div style="font-size: 0.68rem; color: #64748b; margin-bottom: 10px;">ID Registro: OKF-MED-7412-2026 | Protocolo UCI Nivel II</div>
                <div class="pdf-meta-box">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 4px;">
                        <div><b>Paciente:</b> {st.session_state['active_case']['patient_name']}</div>
                        <div><b>Doc. ID:</b> {st.session_state['active_case']['cedula']}</div>
                        <div><b>Servicio:</b> {st.session_state['active_case']['ward']}</div>
                        <div><b>Ubicación:</b> {st.session_state['active_case']['bed']}</div>
                    </div>
                </div>
                <div style="font-weight: 700; color: #0f172a; margin-bottom: 4px;">Signos Vitales al Ingreso</div>
                <table class="pdf-table">
                    <tr>
                        <th>Frec. Cardíaca</th>
                        <td>{st.session_state['active_case']['vital_signs']['heart_rate']} lpm</td>
                        <th>Frec. Resp.</th>
                        <td>{st.session_state['active_case']['vital_signs']['respiratory_rate']} rpm</td>
                    </tr>
                    <tr>
                        <th>Presión Arterial</th>
                        <td>{st.session_state['active_case']['vital_signs']['blood_pressure']}</td>
                        <th>Temperatura</th>
                        <td>{st.session_state['active_case']['vital_signs']['temperature']}</td>
                    </tr>
                    <tr>
                        <th>Saturación O2</th>
                        <td>{st.session_state['active_case']['vital_signs']['oxygen_saturation']}</td>
                        <th>Triage</th>
                        <td><span style="color: #b91c1c; font-weight: 700;">Prioridad II</span></td>
                    </tr>
                </table>
                <div style="font-weight: 700; color: #0f172a; margin-bottom: 4px;">Hallazgos y Observaciones de Enfermería</div>
                <div style="font-size: 0.72rem; color: #334155; margin-bottom: 8px;">
                    {st.session_state['active_case']['observations']}
                </div>
                <div style="font-weight: 700; color: #0f172a; margin-bottom: 4px;">Intervenciones Inmediatas Ejecutadas</div>
                <ul style="margin: 0; padding-left: 16px; font-size: 0.7rem; color: #334155; margin-bottom: 12px;">
                    <li>Monitorización electrocardiográfica continua en cama UCI-04.</li>
                    <li>Soporte de oxígeno por cánula a 2 L/min logrando SpO2 de 97%.</li>
                    <li>Acceso venoso permeable y extracción de analíticas de control.</li>
                </ul>
                <div style="border-top: 1px solid #cbd5e1; padding-top: 8px; display: flex; justify-content: space-between; align-items: flex-end;">
                    <div>
                        <div style="font-size: 0.65rem; color: #64748b;">Enfermera Responsable</div>
                        <div style="font-weight: 700; font-size: 0.74rem; color: #0f172a;">{st.session_state['active_case']['nurse']}</div>
                    </div>
                    <div style="text-align: right;">
                        <span style="font-size: 0.65rem; color: #059669; font-weight: 700;">✓ Firma Digital Certificada</span>
                    </div>
                </div>
            </div>
        </div>
        """)

        # GENERACIÓN REAL DEL PDF Y BOTONES DE ACCIÓN
        try:
            # Generamos el PDF real en disco con ReportLab
            real_pdf_path = pdf_gen.generate(st.session_state["active_case"], st.session_state["active_case"]["patient_id"])
            pdf_bytes = Path(real_pdf_path).read_bytes()

            st.download_button(
                label="📥 Descargar PDF (Generar)",
                data=pdf_bytes,
                file_name=f"{st.session_state['active_case']['patient_id']}_reporte_clinico.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="btn_dl_main_pdf"
            )
        except Exception as e:
            st.error(f"Error generando PDF: {e}")

        # BOTÓN: ENVIAR A HISTORIA CLÍNICA (SQLITE)
        if st.button("💾 Enviar a Historia Clínica", key="btn_save_db"):
            try:
                db.upsert_patient(st.session_state["active_case"]["patient_id"], st.session_state["active_case"])
                note_id = db.save_note(
                    st.session_state["active_case"]["patient_id"],
                    st.session_state["active_case"],
                    pdf_path=str(real_pdf_path) if 'real_pdf_path' in locals() else None
                )
                st.success(f"✓ Registrado con éxito en Historia Clínica (Nota #{note_id})")
            except Exception as e:
                st.error(f"Error guardando en base de datos: {e}")

# ------------------------------------------------------------------------------
# PESTAÑA 2: NOTA POR IMAGEN (GEMMA VISION)
# ------------------------------------------------------------------------------
with tab_img:
    render_html("""
    <div style="margin-bottom: 16px;">
        <h3 style="color: #ffffff; font-weight: 700; margin: 0;">📷 Digitalización de Notas Manuscritas</h3>
        <p style="color: #94a3b8; font-size: 0.88rem; margin-top: 4px;">Sube una fotografía de la orden médica o nota manuscrita para extraer los signos vitales y datos clínicos con Gemma Vision.</p>
    </div>
    """)

    col_up_izq, col_up_der = st.columns([1, 1], gap="large")

    with col_up_izq:
        pid_img = st.text_input("Identificador / Cédula del Paciente *", placeholder="Ej: P-186602023", key="pid_img_field")
        foto_subida = st.file_uploader("Seleccionar imagen de la nota *", type=["jpg", "jpeg", "png", "webp"], key="img_file_up")

        if foto_subida:
            st.image(foto_subida, caption="Vista previa de nota manuscrita", use_container_width=True)

        campos_img_validos = bool(pid_img.strip() and foto_subida)
        btn_proc_img = st.button("🚀 Extraer Datos con Gemma Vision", disabled=not (campos_img_validos and api_key_ok), key="btn_proc_img")

        if not api_key_ok:
            st.info("💡 Puedes ingresar tu Google API Key en la barra lateral izquierda para procesar imágenes en vivo.")

    with col_up_der:
        if btn_proc_img and campos_img_validos:
            from agent.gemma_vision import GemmaVisionAgent
            sufijo = "." + foto_subida.name.split(".")[-1]
            with tempfile.NamedTemporaryFile(suffix=sufijo, delete=False) as tmp:
                tmp.write(foto_subida.getbuffer())
                ruta_tmp = tmp.name

            with st.status("🔍 Analizando caligrafía médica con Gemma Vision...", expanded=True) as status:
                try:
                    agente_v = GemmaVisionAgent()
                    nota_extraida = agente_v.analyze_image(ruta_tmp)
                    if not nota_extraida.get("patient_id"):
                        nota_extraida["patient_id"] = pid_img

                    # Guardar en pipeline
                    okf_path = okf_conv.save(nota_extraida, pid_img)
                    pdf_path = pdf_gen.generate(nota_extraida, pid_img)
                    db.upsert_patient(pid_img, nota_extraida)
                    note_id = db.save_note(pid_img, nota_extraida, okf_path=okf_path, pdf_path=pdf_path)

                    # Actualizar sesión activa
                    st.session_state["active_case"] = nota_extraida
                    status.update(label=f"✓ Procesamiento completado (Nota #{note_id})", state="complete")
                    st.success("¡Datos extraídos con éxito! El Dashboard Clínico ha sido actualizado.")
                    st.json(nota_extraida)
                except Exception as e:
                    status.update(label="❌ Error al procesar imagen", state="error")
                    st.error(str(e))
                finally:
                    try:
                        os.unlink(ruta_tmp)
                    except Exception:
                        pass

# ------------------------------------------------------------------------------
# PESTAÑA 3: NOTA POR VOZ (GEMINI AUDIO)
# ------------------------------------------------------------------------------
with tab_voz:
    render_html("""
    <div style="margin-bottom: 16px;">
        <h3 style="color: #ffffff; font-weight: 700; margin: 0;">🎙️ Dictado Clínico por Voz</h3>
        <p style="color: #94a3b8; font-size: 0.88rem; margin-top: 4px;">Dicta la nota de evolución clínica. Gemini transcribe y estructura automáticamente los signos vitales y tratamientos.</p>
    </div>
    """)

    col_v_izq, col_v_der = st.columns([1, 1], gap="large")

    with col_v_izq:
        pid_voz = st.text_input("Identificador del Paciente *", placeholder="Ej: P-186602023", key="pid_voz_field")
        audio_mic = st.audio_input("Grabar nota desde el micrófono", key="audio_mic_rec")
        audio_file = st.file_uploader("O subir archivo de audio grabado", type=["wav", "mp3", "ogg", "m4a"], key="audio_file_up")

        audio_listo = audio_mic or audio_file
        if audio_listo:
            st.audio(audio_listo)

        btn_proc_voz = st.button("🚀 Transcribir y Extraer con Gemini", disabled=not (bool(pid_voz.strip()) and audio_listo and api_key_ok), key="btn_proc_voz")

    with col_v_der:
        if btn_proc_voz and audio_listo:
            from agent.gemma_vision import GemmaVisionAgent
            raw_audio = audio_listo.getvalue()
            mime_type = "audio/wav" if audio_mic else "audio/mp3"

            with st.status("🎧 Procesando audio y estructurando nota clínica...", expanded=True) as status:
                try:
                    agente_v = GemmaVisionAgent()
                    nota_audio = agente_v.analyze_audio(raw_audio, mime_type=mime_type)
                    if not nota_audio.get("patient_id"):
                        nota_audio["patient_id"] = pid_voz

                    okf_path = okf_conv.save(nota_audio, pid_voz)
                    pdf_path = pdf_gen.generate(nota_audio, pid_voz)
                    db.upsert_patient(pid_voz, nota_audio)
                    note_id = db.save_note(pid_voz, nota_audio, okf_path=okf_path, pdf_path=pdf_path)

                    st.session_state["active_case"] = nota_audio
                    status.update(label=f"✓ Nota #{note_id} registrada con éxito", state="complete")
                    st.success("¡Nota por voz procesada y registrada en el Dashboard!")
                    st.json(nota_audio)
                except Exception as e:
                    status.update(label="❌ Error al procesar audio", state="error")
                    st.error(str(e))

# ------------------------------------------------------------------------------
# PESTAÑA 4: HISTORIAL DE PACIENTE
# ------------------------------------------------------------------------------
with tab_hist:
    st.subheader("📋 Búsqueda en Historia Clínica Electrónica")
    busc_id = st.text_input("ID o Cédula del Paciente a consultar", value="P-186602023", key="busc_hist_id")
    
    if st.button("🔍 Consultar Expediente", key="btn_cons_hist"):
        pac = db.get_patient(busc_id.strip())
        if not pac:
            st.info(f"Paciente '{busc_id}' no encontrado en la base de datos local. Puedes registrarlo desde el Dashboard o subir una nota.")
        else:
            st.success(f"Expediente encontrado: **{pac['patient_name']}**")
            notas = db.get_patient_notes(busc_id.strip())
            st.markdown(f"**Total de evoluciones clínicas registradas: {len(notas)}**")
            for idx, n in enumerate(notas, 1):
                with st.expander(f"Evolución #{n['id']} — {n.get('date', 'Sin fecha')} ({n.get('time', '')})", expanded=(idx==1)):
                    st.write(n["note_data"])

# ------------------------------------------------------------------------------
# PESTAÑA 5: DIRECTORIO DE PACIENTES
# ------------------------------------------------------------------------------
with tab_pacs:
    st.subheader("👥 Censo de Pacientes Hospitalizados")
    pacs = db.list_patients()
    if not pacs:
        # Si no hay pacientes aún, mostramos el caso demo como registro de referencia
        st.info("Mostrando censo hospitalario de referencia (1 paciente activo en UCI).")
        st.dataframe([
            {
                "ID": DEMO_CASE["patient_id"],
                "Nombre": DEMO_CASE["patient_name"],
                "Servicio": DEMO_CASE["ward"],
                "Cama": DEMO_CASE["bed"],
                "Estado": DEMO_CASE["status"],
                "Última Evaluación": DEMO_CASE["date"]
            }
        ], use_container_width=True)
    else:
        st.dataframe([
            {
                "ID": p["patient_id"],
                "Nombre": p["patient_name"],
                "Servicio": p.get("ward", "General"),
                "Cama": p.get("bed", "-"),
                "Notas": p.get("total_notes", 0),
                "Actualizado": p["updated_at"][:16].replace("T", " ")
            }
            for p in pacs
        ], use_container_width=True)
