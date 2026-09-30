# =============================================================
# main.py — CLI principal del Agente Persistente de Enfermería
#
# Este es el punto de entrada del programa. Usa Typer para
# crear una interfaz de línea de comandos con múltiples comandos.
#
# Comandos disponibles:
#   process      → Analiza imagen y ejecuta pipeline completo
#   history      → Muestra historial de notas de un paciente
#   update       → Actualiza paciente con nueva imagen
#   list-patients→ Lista todos los pacientes registrados
#   export-pdf   → Regenera el PDF de la última nota
# =============================================================

# pathlib.Path: manejo de rutas de archivos multiplataforma
from pathlib import Path

# sys: para salida con código de error cuando hay excepciones
import sys

# os: para verificar existencia de archivos y rutas
import os

# json: para mostrar datos JSON en el historial
import json

# dotenv: carga las variables del archivo .env ANTES de todo lo demás
# Esto es crítico: debe ser la primera importación que ejecute código
from dotenv import load_dotenv

# Cargamos .env inmediatamente al inicio del programa
# override=False → no sobreescribe variables ya definidas en el sistema
load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=False)

# typer: framework para crear CLIs elegantes en Python
# app es el objeto principal de la aplicación CLI
import typer

# rich: librería para mostrar texto con formato, colores y tablas en terminal
from rich.console import Console      # Consola con soporte de colores
from rich.panel import Panel          # Cuadros de texto con bordes
from rich.table import Table          # Tablas formateadas en terminal
from rich.text import Text            # Texto con formato/colores
from rich.progress import track       # Barra de progreso para operaciones largas
from rich import print as rprint      # print() con soporte de markup Rich

# Importamos los módulos del agente (todos en la carpeta agent/)
from agent.gemma_vision import GemmaVisionAgent    # Análisis de imagen con Gemma
from agent.okf_converter import OKFConverter        # Conversión a OKF/JSON-LD
from agent.pdf_generator import PDFGenerator        # Generación de PDF
from agent.persistence import NurseDatabase         # Base de datos SQLite

# ─────────────────────────────────────────────
# Inicialización de la aplicación
# ─────────────────────────────────────────────

# Objeto principal de Typer (orquesta todos los subcomandos)
app = typer.Typer(
    name="nurse-agent",                               # Nombre del programa
    help="🏥 Agente persistente de notas de enfermería con Gemma + OKF + PDF",
    add_completion=False,                             # Deshabilitamos autocomplete
    rich_markup_mode="rich",                          # Soporte de Rich en el help
)

# Consola Rich para output con colores y estilos
console = Console()

# Instancias de los módulos del agente
# Las instanciamos a nivel de módulo para reutilizarlas entre comandos
db = NurseDatabase()              # Base de datos persistente
okf = OKFConverter()              # Convertidor OKF
pdf_gen = PDFGenerator()          # Generador de PDF


# ─────────────────────────────────────────────
# Función auxiliar: ejecutar pipeline completo
# ─────────────────────────────────────────────
def _run_pipeline(image_path: str, patient_id: str) -> dict:
    """
    Ejecuta el pipeline completo para una imagen:
    Imagen → JSON (Gemma) → OKF → PDF → SQLite

    Esta función centraliza la lógica del pipeline para que
    tanto 'process' como 'update' puedan reutilizarla.

    Args:
        image_path: Ruta a la imagen de la nota manuscrita
        patient_id: ID del paciente al que pertenece la nota

    Returns:
        Diccionario con los resultados del pipeline:
        {nota, okf_path, pdf_path, note_id}
    """
    # Paso 1: Análisis de imagen con Gemma (IA multimodal)
    console.print("\n[bold blue]📷 Paso 1/4:[/] Analizando imagen con Gemma...")

    # Instanciamos el agente de visión (aquí se valida la API key)
    agente = GemmaVisionAgent()

    # Enviamos la imagen al modelo y recibimos el JSON estructurado
    nota = agente.analyze_image(image_path)

    console.print(f"  [green]✓[/] JSON extraído: {len(nota)} campos procesados")

    # Si la nota no tiene patient_id, usamos el proporcionado por CLI
    if not nota.get("patient_id"):
        nota["patient_id"] = patient_id
        console.print(f"  [yellow]ℹ[/] ID asignado manualmente: {patient_id}")

    # Paso 2: Convertir JSON → OKF (JSON-LD semántico)
    console.print("\n[bold blue]📄 Paso 2/4:[/] Convirtiendo a formato OKF (JSON-LD)...")
    okf_path = okf.save(nota, patient_id)
    console.print(f"  [green]✓[/] OKF guardado: [dim]{okf_path}[/]")

    # Paso 3: Generar PDF del reporte
    console.print("\n[bold blue]📑 Paso 3/4:[/] Generando reporte PDF...")
    pdf_path = pdf_gen.generate(nota, patient_id)
    console.print(f"  [green]✓[/] PDF generado: [dim]{pdf_path}[/]")

    # Paso 4: Persistir en base de datos SQLite
    console.print("\n[bold blue]💾 Paso 4/4:[/] Guardando en base de datos...")

    # Creamos o actualizamos el registro del paciente
    db.upsert_patient(patient_id, nota)

    # Guardamos la nota en el historial
    note_id = db.save_note(patient_id, nota, okf_path=okf_path, pdf_path=pdf_path)
    console.print(f"  [green]✓[/] Nota #{note_id} persistida para paciente {patient_id}")

    return {
        "nota": nota,
        "okf_path": okf_path,
        "pdf_path": pdf_path,
        "note_id": note_id,
    }


# ─────────────────────────────────────────────
# Comando: process
# ─────────────────────────────────────────────
@app.command()
def process(
    image: str = typer.Option(..., "--image", "-i", help="Ruta a la imagen de la nota de enfermería"),
    patient_id: str = typer.Option(..., "--patient-id", "-p", help="ID único del paciente (ej. P001)"),
):
    """
    📷 Procesa una imagen nueva de nota de enfermería.

    Pipeline completo: Imagen → JSON (Gemma) → OKF → PDF → Base de datos
    """
    console.print(Panel.fit(
        f"[bold]🏥 AGENTE DE ENFERMERÍA[/]\n"
        f"Procesando nota para paciente: [cyan]{patient_id}[/]\n"
        f"Imagen: [dim]{image}[/]",
        border_style="blue"
    ))

    try:
        # Verificamos que la imagen exista antes de llamar a Gemma
        if not Path(image).exists():
            console.print(f"[red]❌ Error: No se encuentra la imagen '{image}'[/]")
            raise typer.Exit(1)

        # Ejecutamos el pipeline completo
        resultado = _run_pipeline(image, patient_id)

        # Mostramos resumen del resultado
        console.print(Panel.fit(
            f"[bold green]✅ Pipeline completado con éxito[/]\n\n"
            f"📋 Nota #[cyan]{resultado['note_id']}[/] guardada\n"
            f"📄 OKF: [dim]{resultado['okf_path']}[/]\n"
            f"📑 PDF: [dim]{resultado['pdf_path']}[/]",
            border_style="green",
            title="Resultado"
        ))

    except ValueError as e:
        # Error de validación (API key no configurada, JSON inválido, etc.)
        console.print(f"[red]{e}[/]")
        raise typer.Exit(1)

    except Exception as e:
        # Error inesperado
        console.print(f"[red]❌ Error inesperado: {e}[/]")
        raise typer.Exit(1)


# ─────────────────────────────────────────────
# Comando: update
# ─────────────────────────────────────────────
@app.command()
def update(
    image: str = typer.Option(..., "--image", "-i", help="Nueva imagen con nota actualizada"),
    patient_id: str = typer.Option(..., "--patient-id", "-p", help="ID del paciente a actualizar"),
):
    """
    🔄 Actualiza un paciente existente con una nueva imagen.

    Si el paciente no existe, lo crea. Si ya existe, agrega la nueva
    nota al historial manteniendo todas las anteriores (persistencia).
    """
    console.print(Panel.fit(
        f"[bold]🔄 ACTUALIZACIÓN DE PACIENTE[/]\n"
        f"Paciente: [cyan]{patient_id}[/]",
        border_style="yellow"
    ))

    # Verificamos si el paciente ya existe en la base de datos
    paciente_existente = db.get_patient(patient_id)

    if paciente_existente:
        # Informamos cuántas notas tiene ya este paciente
        notas_previas = db.get_patient_notes(patient_id)
        console.print(
            f"[yellow]ℹ[/] Paciente [cyan]{patient_id}[/] encontrado con "
            f"[bold]{len(notas_previas)}[/] nota(s) previa(s)."
        )
    else:
        # Si no existe, el pipeline lo creará automáticamente
        console.print(
            f"[yellow]ℹ[/] Paciente [cyan]{patient_id}[/] no existe. Se creará."
        )

    try:
        # El pipeline es el mismo para 'process' y 'update'
        # La diferencia es que 'update' informa si el paciente ya tenía historial
        resultado = _run_pipeline(image, patient_id)

        # Mensaje de confirmación con cuántas notas tiene ahora el paciente
        notas_totales = db.get_patient_notes(patient_id)
        console.print(Panel.fit(
            f"[bold green]✅ Paciente actualizado[/]\n\n"
            f"Total de notas: [cyan]{len(notas_totales)}[/]\n"
            f"Última nota #[cyan]{resultado['note_id']}[/]\n"
            f"📑 PDF: [dim]{resultado['pdf_path']}[/]",
            border_style="green",
            title="Actualización completada"
        ))

    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/]")
        raise typer.Exit(1)


# ─────────────────────────────────────────────
# Comando: history
# ─────────────────────────────────────────────
@app.command()
def history(
    patient_id: str = typer.Option(..., "--patient-id", "-p", help="ID del paciente"),
    limit: int = typer.Option(10, "--limit", "-n", help="Número máximo de notas a mostrar"),
):
    """
    📚 Muestra el historial de notas de un paciente.

    Lista las notas de más reciente a más antigua, con la
    información clave de cada una.
    """
    # Buscamos el paciente en la base de datos
    paciente = db.get_patient(patient_id)

    if not paciente:
        # Si el paciente no existe, informamos y salimos
        console.print(f"[red]❌ Paciente '{patient_id}' no encontrado.[/]")
        console.print("[dim]Usa 'process' o 'update' para registrar al paciente primero.[/]")
        raise typer.Exit(1)

    # Mostramos los datos básicos del paciente en un panel
    console.print(Panel.fit(
        f"[bold]👤 Paciente:[/] [cyan]{paciente['patient_name']}[/]\n"
        f"[bold]ID:[/] {paciente['patient_id']}  |  "
        f"[bold]Sala:[/] {paciente.get('ward', '—')}  |  "
        f"[bold]Cama:[/] {paciente.get('bed', '—')}\n"
        f"[bold]Registrado:[/] {paciente['created_at'][:10]}  |  "
        f"[bold]Última actualización:[/] {paciente['updated_at'][:10]}",
        title="📋 Expediente del Paciente",
        border_style="blue"
    ))

    # Obtenemos el historial de notas
    notas = db.get_patient_notes(patient_id)

    if not notas:
        console.print("[yellow]No hay notas registradas para este paciente.[/]")
        return

    console.print(f"\n[bold]Mostrando {min(limit, len(notas))} de {len(notas)} nota(s):[/]\n")

    # Creamos una tabla Rich para mostrar el historial visualmente
    tabla = Table(
        show_header=True,
        header_style="bold blue",
        border_style="dim",
        expand=True,
    )

    # Definimos las columnas de la tabla
    tabla.add_column("#", style="dim", width=4)          # Número de la nota
    tabla.add_column("ID Nota", style="cyan", width=8)    # ID en BD
    tabla.add_column("Fecha", width=10)                   # Fecha de la nota
    tabla.add_column("Hora", width=6)                     # Hora de la nota
    tabla.add_column("Enfermera", width=18)               # Enfermera responsable
    tabla.add_column("Síntomas", width=25)                # Primeros síntomas
    tabla.add_column("PDF", width=20)                     # Ruta corta al PDF

    # Agregamos las filas (limitadas por el parámetro --limit)
    for i, nota in enumerate(notas[:limit], 1):
        note_data = nota["note_data"]  # Diccionario con los datos de la nota

        # Obtenemos los primeros 2 síntomas para mostrar en la tabla
        sintomas = note_data.get("symptoms", [])
        sintomas_texto = ", ".join(sintomas[:2]) if sintomas else "—"
        if len(sintomas) > 2:
            sintomas_texto += f" +{len(sintomas)-2}"  # "+3" si hay más

        # Acortamos la ruta del PDF para que quepa en la tabla
        pdf_path = nota.get("pdf_path", "—")
        if pdf_path and len(str(pdf_path)) > 18:
            pdf_path = "..." + str(pdf_path)[-15:]  # Solo los últimos 15 chars

        tabla.add_row(
            str(i),                                          # Número correlativo
            str(nota["id"]),                                 # ID en la base de datos
            str(nota.get("date") or "—"),                   # Fecha
            str(nota.get("time") or "—"),                   # Hora
            str(nota.get("nurse") or "—"),                  # Enfermera
            sintomas_texto,                                  # Síntomas resumidos
            str(pdf_path),                                   # Ruta PDF
        )

    # Imprimimos la tabla en la terminal
    console.print(tabla)


# ─────────────────────────────────────────────
# Comando: list-patients
# ─────────────────────────────────────────────
@app.command(name="list-patients")
def list_patients():
    """
    👥 Lista todos los pacientes registrados en el sistema.
    """
    # Obtenemos todos los pacientes de la base de datos
    pacientes = db.list_patients()

    if not pacientes:
        # Si no hay pacientes, mostramos un mensaje informativo
        console.print(Panel.fit(
            "[yellow]No hay pacientes registrados todavía.[/]\n"
            "Usa [bold]process --image IMAGEN --patient-id ID[/] para agregar el primero.",
            border_style="yellow"
        ))
        return

    # Encabezado de la lista
    console.print(Panel.fit(
        f"[bold]👥 {len(pacientes)} paciente(s) registrado(s)[/]",
        border_style="blue"
    ))

    # Tabla con todos los pacientes
    tabla = Table(
        show_header=True,
        header_style="bold blue",
        border_style="dim",
        expand=True,
    )

    # Columnas de la tabla de pacientes
    tabla.add_column("ID", style="cyan", width=10)
    tabla.add_column("Nombre", width=25)
    tabla.add_column("Sala", width=12)
    tabla.add_column("Cama", width=8)
    tabla.add_column("Notas", justify="center", width=6)
    tabla.add_column("Último registro", width=18)

    # Agregamos una fila por cada paciente
    for p in pacientes:
        tabla.add_row(
            p["patient_id"],                         # ID del paciente
            p["patient_name"],                       # Nombre completo
            p.get("ward") or "—",                   # Sala (puede ser null)
            p.get("bed") or "—",                    # Cama (puede ser null)
            str(p.get("total_notes", 0)),            # Total de notas en historial
            p["updated_at"][:16].replace("T", " "), # Fecha/hora legible
        )

    console.print(tabla)


# ─────────────────────────────────────────────
# Comando: export-pdf
# ─────────────────────────────────────────────
@app.command(name="export-pdf")
def export_pdf(
    patient_id: str = typer.Option(..., "--patient-id", "-p", help="ID del paciente"),
):
    """
    📄 Regenera el PDF de la nota más reciente de un paciente.

    Útil si el PDF anterior se eliminó o se necesita una copia nueva.
    """
    # Verificamos que el paciente exista
    if not db.get_patient(patient_id):
        console.print(f"[red]❌ Paciente '{patient_id}' no encontrado.[/]")
        raise typer.Exit(1)

    # Obtenemos la nota más reciente del paciente
    ultima_nota = db.get_latest_note(patient_id)

    if not ultima_nota:
        console.print(f"[yellow]⚠ No hay notas para el paciente '{patient_id}'.[/]")
        raise typer.Exit(1)

    console.print(f"[blue]📑 Regenerando PDF para paciente [cyan]{patient_id}[/]...[/]")

    # Extraemos los datos de la nota
    note_data = ultima_nota["note_data"]

    # Generamos el nuevo PDF
    pdf_path = pdf_gen.generate(note_data, patient_id)

    # Actualizamos la ruta del PDF en la base de datos
    db.update_note_paths(ultima_nota["id"], pdf_path=pdf_path)

    console.print(Panel.fit(
        f"[green]✅ PDF regenerado exitosamente[/]\n"
        f"📑 [dim]{pdf_path}[/]",
        border_style="green"
    ))


# ─────────────────────────────────────────────
# Punto de entrada del programa
# ─────────────────────────────────────────────
if __name__ == "__main__":
    # Typer.app() es el entry point que lee los argumentos del CLI
    # y despacha al comando correspondiente
    try:
        app()
    finally:
        # Siempre cerramos la conexión a la base de datos al terminar
        # Esto garantiza que los datos se flush-en correctamente a disco
        db.close()
