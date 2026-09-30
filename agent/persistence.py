# =============================================================
# agent/persistence.py
# Capa de persistencia del agente: almacena y recupera los
# datos de pacientes y sus notas de enfermería usando SQLite.
#
# SQLite es una base de datos embebida (sin servidor) que
# guarda todo en un único archivo .db. Es perfecta para
# aplicaciones de escritorio y agentes locales.
#
# Tablas:
#   patients  → Un registro por paciente (datos básicos)
#   notes     → Múltiples notas por paciente (historial)
# =============================================================

# sqlite3: módulo estándar de Python para trabajar con SQLite
# No requiere instalación adicional, viene incluido en Python
import sqlite3

# json: para serializar/deserializar datos complejos (listas, dicts)
# SQLite no soporta JSON nativo, así que los guardamos como texto
import json

# datetime: para registrar cuándo se creó o actualizó cada nota
import datetime

# os y Path: para construir la ruta de la base de datos
import os
from pathlib import Path

# Optional y List: anotaciones de tipo para los retornos de funciones
from typing import Optional, List


# ─────────────────────────────────────────────
# Clase principal de persistencia
# ─────────────────────────────────────────────
class NurseDatabase:
    """
    Gestiona el almacenamiento persistente de pacientes y notas
    de enfermería en una base de datos SQLite local.

    Esta clase implementa el patrón Repository: abstrae los
    detalles de la base de datos del resto de la aplicación.
    """

    def __init__(self):
        """
        Constructor: conecta a la base de datos SQLite y crea
        las tablas si no existen todavía.
        """
        # Leemos la ruta del archivo .db desde la variable de entorno
        db_path_str = os.getenv("DB_PATH", "./data/patients.db")

        # Convertimos a Path y creamos el directorio padre si no existe
        self.db_path = Path(db_path_str)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Conectamos a SQLite. check_same_thread=False permite usar la
        # conexión desde distintos contextos sin errores de threading
        self.conn = sqlite3.connect(
            str(self.db_path),
            check_same_thread=False
        )

        # Habilitamos el modo WAL (Write-Ahead Logging) para mejor
        # rendimiento en lecturas concurrentes y mayor durabilidad
        self.conn.execute("PRAGMA journal_mode=WAL")

        # Habilitamos claves foráneas para integridad referencial
        self.conn.execute("PRAGMA foreign_keys=ON")

        # row_factory hace que las filas devueltas sean como diccionarios
        # Permite acceder a columnas por nombre: row["patient_name"]
        self.conn.row_factory = sqlite3.Row

        # Creamos las tablas si todavía no existen
        self._crear_tablas()

    def _crear_tablas(self):
        """
        Crea el esquema de la base de datos (si no existe ya).
        Usa CREATE TABLE IF NOT EXISTS para ser idempotente
        (se puede llamar múltiples veces sin errores).
        """
        # Cursor para ejecutar sentencias SQL
        cursor = self.conn.cursor()

        # ── Tabla de pacientes ────────────────────────────────
        # Un registro por paciente; se actualiza cuando hay nueva nota
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                patient_id    TEXT PRIMARY KEY,
                patient_name  TEXT NOT NULL,
                ward          TEXT,
                bed           TEXT,
                created_at    TEXT NOT NULL,
                updated_at    TEXT NOT NULL
            )
        """)
        # patient_id: identificador único del paciente (clave primaria)
        # patient_name: nombre completo
        # ward: sala o área hospitalaria
        # bed: número de cama
        # created_at: fecha de primer registro (ISO 8601)
        # updated_at: fecha de última actualización

        # ── Tabla de notas ────────────────────────────────────
        # Múltiples notas por paciente (historial completo)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id    TEXT NOT NULL,
                date          TEXT,
                time          TEXT,
                nurse         TEXT,
                raw_json      TEXT NOT NULL,
                okf_path      TEXT,
                pdf_path      TEXT,
                created_at    TEXT NOT NULL,
                FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
            )
        """)
        # id: clave primaria autoincremental (entero)
        # patient_id: referencia al paciente (clave foránea)
        # date / time: fecha y hora de la nota (extraídas de la imagen)
        # nurse: nombre de la enfermera que escribió la nota
        # raw_json: nota completa serializada como texto JSON
        # okf_path: ruta al archivo .jsonld generado (puede ser null)
        # pdf_path: ruta al archivo .pdf generado (puede ser null)
        # created_at: cuándo se procesó la imagen

        # Guardamos los cambios en disco
        self.conn.commit()

    def upsert_patient(self, patient_id: str, nota: dict):
        """
        Crea o actualiza un registro de paciente.

        Si el paciente ya existe (mismo patient_id), actualiza
        sus datos básicos con la información más reciente.
        Si no existe, crea un registro nuevo.

        'Upsert' = UPDATE + INSERT (fusión de ambas operaciones)

        Args:
            patient_id: ID único del paciente
            nota: Diccionario con los datos de la nota de enfermería
        """
        ahora = datetime.datetime.now().isoformat()  # Timestamp actual

        # INSERT OR REPLACE es el upsert de SQLite:
        # - Si patient_id no existe → inserta fila nueva
        # - Si patient_id ya existe → reemplaza con los nuevos valores
        self.conn.execute(
            """
            INSERT INTO patients (patient_id, patient_name, ward, bed, created_at, updated_at)
            VALUES (?, ?, ?, ?, COALESCE(
                (SELECT created_at FROM patients WHERE patient_id = ?),
                ?
            ), ?)
            ON CONFLICT(patient_id) DO UPDATE SET
                patient_name = excluded.patient_name,
                ward         = excluded.ward,
                bed          = excluded.bed,
                updated_at   = excluded.updated_at
            """,
            (
                patient_id,                         # patient_id
                nota.get("patient_name", "—"),       # patient_name
                nota.get("ward"),                    # ward
                nota.get("bed"),                     # bed
                patient_id,                         # para COALESCE subconsulta
                ahora,                              # created_at (nuevo registro)
                ahora,                              # updated_at
            )
        )
        self.conn.commit()

    def save_note(self, patient_id: str, nota: dict,
                  okf_path: str = None, pdf_path: str = None) -> int:
        """
        Guarda una nueva nota de enfermería en la base de datos.
        Cada llamada agrega un nuevo registro al historial del paciente.

        Args:
            patient_id: ID del paciente al que pertenece la nota
            nota: Diccionario completo de la nota de enfermería
            okf_path: Ruta al archivo OKF generado (opcional)
            pdf_path: Ruta al archivo PDF generado (opcional)

        Returns:
            El ID autoincremental de la nota recién insertada
        """
        ahora = datetime.datetime.now().isoformat()

        # Serializamos el diccionario completo a JSON para guardarlo en SQLite
        # ensure_ascii=False preserva tildes y caracteres especiales
        raw_json = json.dumps(nota, ensure_ascii=False, indent=2)

        # Insertamos la nota en la tabla 'notes'
        cursor = self.conn.execute(
            """
            INSERT INTO notes
                (patient_id, date, time, nurse, raw_json, okf_path, pdf_path, created_at)
            VALUES
                (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                patient_id,                # patient_id (FK → patients)
                nota.get("date"),          # fecha de la nota
                nota.get("time"),          # hora de la nota
                nota.get("nurse"),         # enfermera responsable
                raw_json,                  # JSON completo serializado
                str(okf_path) if okf_path else None,  # ruta OKF
                str(pdf_path) if pdf_path else None,  # ruta PDF
                ahora,                     # timestamp de procesamiento
            )
        )
        self.conn.commit()

        # Retornamos el ID de la nota recién creada
        return cursor.lastrowid

    def get_patient(self, patient_id: str) -> Optional[dict]:
        """
        Busca un paciente por su ID.

        Args:
            patient_id: ID del paciente a buscar

        Returns:
            Diccionario con los datos del paciente, o None si no existe
        """
        # Ejecutamos la consulta SELECT con el patient_id como filtro
        row = self.conn.execute(
            "SELECT * FROM patients WHERE patient_id = ?",
            (patient_id,)
        ).fetchone()  # fetchone devuelve la primera fila o None

        # Convertimos el objeto Row a diccionario Python (si existe)
        return dict(row) if row else None

    def get_patient_notes(self, patient_id: str) -> List[dict]:
        """
        Obtiene el historial completo de notas de un paciente,
        ordenadas de la más reciente a la más antigua.

        Args:
            patient_id: ID del paciente

        Returns:
            Lista de diccionarios, cada uno con los datos de una nota
        """
        # Ordenamos por created_at DESC para ver primero las más recientes
        rows = self.conn.execute(
            """
            SELECT * FROM notes
            WHERE patient_id = ?
            ORDER BY created_at DESC
            """,
            (patient_id,)
        ).fetchall()  # fetchall devuelve todas las filas

        # Convertimos cada Row a dict y parseamos el raw_json guardado
        notas = []
        for row in rows:
            nota_dict = dict(row)  # Convertir Row a dict
            # Deserializamos el JSON guardado como texto de vuelta a dict
            nota_dict["note_data"] = json.loads(nota_dict["raw_json"])
            notas.append(nota_dict)

        return notas

    def list_patients(self) -> List[dict]:
        """
        Lista todos los pacientes registrados en la base de datos,
        ordenados por fecha de última actualización.

        Returns:
            Lista de diccionarios con los datos básicos de cada paciente
        """
        rows = self.conn.execute(
            """
            SELECT
                p.*,
                COUNT(n.id) as total_notes
            FROM patients p
            LEFT JOIN notes n ON p.patient_id = n.patient_id
            GROUP BY p.patient_id
            ORDER BY p.updated_at DESC
            """
        ).fetchall()

        # Convertimos cada Row a diccionario
        return [dict(row) for row in rows]

    def get_latest_note(self, patient_id: str) -> Optional[dict]:
        """
        Obtiene la nota más reciente de un paciente.

        Args:
            patient_id: ID del paciente

        Returns:
            Diccionario con los datos de la nota más reciente, o None
        """
        row = self.conn.execute(
            """
            SELECT * FROM notes
            WHERE patient_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (patient_id,)
        ).fetchone()

        if not row:
            return None

        nota_dict = dict(row)
        # Parseamos el JSON de la nota
        nota_dict["note_data"] = json.loads(nota_dict["raw_json"])

        return nota_dict

    def update_note_paths(self, note_id: int, okf_path: str = None, pdf_path: str = None):
        """
        Actualiza las rutas de los archivos OKF y PDF de una nota existente.
        Se usa después de regenerar estos archivos.

        Args:
            note_id: ID de la nota a actualizar
            okf_path: Nueva ruta del archivo OKF
            pdf_path: Nueva ruta del archivo PDF
        """
        self.conn.execute(
            """
            UPDATE notes
            SET okf_path = COALESCE(?, okf_path),
                pdf_path = COALESCE(?, pdf_path)
            WHERE id = ?
            """,
            (
                str(okf_path) if okf_path else None,
                str(pdf_path) if pdf_path else None,
                note_id
            )
        )
        self.conn.commit()

    def close(self):
        """
        Cierra la conexión con la base de datos.
        Siempre se debe llamar al finalizar la aplicación.
        """
        self.conn.close()
