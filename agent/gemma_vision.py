# =============================================================
# agent/gemma_vision.py
# Módulo que envía una imagen al modelo Gemma (multimodal)
# y recibe de vuelta un JSON estructurado con los datos de
# la nota de enfermería escrita a mano.
# =============================================================

# Librería estándar de Python para trabajar con fechas y horas
import datetime

# json: convierte texto a diccionario Python (parse del JSON de Gemma)
import json

# os: acceso a variables de entorno y rutas de archivos
import os

# Path: manejo de rutas de archivos de forma multiplataforma
from pathlib import Path

# google.genai: SDK oficial de Google para Gemma/Gemini
# Permite enviar texto + imágenes y recibir respuestas del modelo
from google import genai

# types: contiene las clases para construir el contenido multimodal
from google.genai import types

# PIL.Image: librería Pillow para abrir, validar y manipular imágenes
from PIL import Image

# Importamos el prompt de extracción definido en json_schema.py
from agent.json_schema import EXTRACTION_PROMPT


# ─────────────────────────────────────────────
# Clase principal del módulo de visión
# ─────────────────────────────────────────────
class GemmaVisionAgent:
    """
    Agente de visión que utiliza el modelo Gemma para analizar
    imágenes de notas de enfermería manuscritas y extraer
    los datos en formato JSON estructurado.
    """

    def __init__(self):
        """
        Constructor: inicializa el cliente de Google Gemini/Gemma.
        Lee la API key y el nombre del modelo desde las variables
        de entorno cargadas previamente por python-dotenv.
        """
        # Leemos la API key del entorno (cargada desde .env)
        api_key = os.getenv("GOOGLE_API_KEY")

        # Si no hay API key, el sistema no puede funcionar → error inmediato
        if not api_key or api_key == "pon_tu_api_key_aqui":
            raise ValueError(
                "❌ GOOGLE_API_KEY no está configurada.\n"
                "   Edita el archivo .env y agrega tu clave de API.\n"
                "   Obtén una en: https://aistudio.google.com/app/apikey"
            )

        # Inicializamos el cliente de Gemini con la API key
        # El cliente maneja autenticación, reintentos y conexión
        self.client = genai.Client(api_key=api_key)

        # Leemos el nombre del modelo desde .env
        # Por defecto usamos gemma-4-26b-a4b-it si no está definido
        self.model = os.getenv("GEMMA_MODEL", "gemma-4-26b-a4b-it")

    def _load_image(self, image_path: str) -> Image.Image:
        """
        Carga y valida una imagen desde el sistema de archivos.

        Args:
            image_path: Ruta al archivo de imagen (JPEG, PNG, etc.)

        Returns:
            Objeto PIL.Image listo para ser enviado a Gemma

        Raises:
            FileNotFoundError: Si la imagen no existe en esa ruta
            ValueError: Si el archivo no es una imagen válida
        """
        # Convertimos la ruta a objeto Path para validación más limpia
        path = Path(image_path)

        # Verificamos que el archivo exista en disco
        if not path.exists():
            raise FileNotFoundError(
                f"❌ Imagen no encontrada: {image_path}\n"
                f"   Verifica que la ruta sea correcta."
            )

        # Verificamos que la extensión sea una imagen soportada
        extensiones_validas = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}
        if path.suffix.lower() not in extensiones_validas:
            raise ValueError(
                f"❌ Formato no soportado: {path.suffix}\n"
                f"   Usa uno de: {', '.join(extensiones_validas)}"
            )

        # Abrimos la imagen con Pillow y la convertimos a RGB
        # (forzar RGB elimina problemas con imágenes RGBA o paleta P)
        imagen = Image.open(path).convert("RGB")

        return imagen

    def analyze_image(self, image_path: str) -> dict:
        """
        Función principal: envía la imagen a Gemma y recibe el JSON.

        Proceso:
        1. Carga y valida la imagen
        2. Construye el mensaje multimodal (texto + imagen)
        3. Envía la petición al modelo Gemma
        4. Parsea la respuesta como JSON
        5. Agrega metadata de procesamiento

        Args:
            image_path: Ruta a la imagen de la nota manuscrita

        Returns:
            Diccionario Python con todos los datos extraídos de la nota
        """
        # Paso 1: Cargar la imagen desde disco
        imagen = self._load_image(image_path)

        # Paso 2: Construir el contenido multimodal para Gemma
        # El modelo puede procesar texto + imágenes en el mismo mensaje
        # Primero va el prompt (instrucciones) y luego la imagen
        contenido = [
            # Texto con las instrucciones de extracción
            EXTRACTION_PROMPT,
            # La imagen PIL se pasa directamente (el SDK la codifica internamente)
            imagen,
        ]

        # Paso 3: Enviar la petición al modelo Gemma
        # generate_content es la función principal para inferencia
        respuesta = self.client.models.generate_content(
            model=self.model,       # Nombre del modelo (de .env)
            contents=contenido,     # Lista con prompt + imagen
            config=types.GenerateContentConfig(
                # Temperatura 0.1 → respuestas deterministas y consistentes
                # (importante para extracción estructurada, no creatividad)
                temperature=0.1,
                # Limitamos los tokens de respuesta al necesario para el JSON
                max_output_tokens=4096,
            ),
        )

        # Paso 4: Extraer el texto de la respuesta del modelo
        texto_respuesta = respuesta.text.strip()

        # A veces el modelo devuelve el JSON envuelto en ```json ... ```
        # Limpiamos esos marcadores si están presentes
        if texto_respuesta.startswith("```"):
            # Eliminamos la primera y última línea (marcadores de código)
            lineas = texto_respuesta.split("\n")
            # Buscamos el inicio del JSON (línea con '{')
            inicio = next(
                (i for i, l in enumerate(lineas) if l.strip().startswith("{")),
                1
            )
            # Buscamos el final del JSON (última línea con '}')
            fin = next(
                (i for i in range(len(lineas)-1, -1, -1) if lineas[i].strip().endswith("}")),
                len(lineas)-1
            )
            texto_respuesta = "\n".join(lineas[inicio:fin+1])

        # Intentamos parsear el JSON producido por Gemma
        try:
            datos = json.loads(texto_respuesta)
        except json.JSONDecodeError as e:
            # Si el JSON no es válido, guardamos el texto crudo y lanzamos error
            raise ValueError(
                f"❌ Gemma no devolvió JSON válido.\n"
                f"   Error de parseo: {e}\n"
                f"   Respuesta recibida:\n{texto_respuesta}"
            )

        # Paso 5: Agregar metadata de procesamiento al resultado
        # (útil para auditoría y trazabilidad del proceso)
        datos["_metadata"] = {
            "processed_at": datetime.datetime.now().isoformat(),  # Marca de tiempo
            "model_used": self.model,                             # Modelo que procesó
            "source_image": str(Path(image_path).resolve()),      # Ruta absoluta imagen
            "input_type": "image",                                # Tipo de entrada usada
        }

        return datos

    def analyze_audio(self, audio_bytes: bytes, mime_type: str = "audio/wav") -> dict:
        """
        Analiza un audio de voz con Gemini y extrae los datos de la nota
        de enfermería dictada verbalmente.

        La enfermera puede dictar la nota en lugar de escribirla a mano.
        Gemini transcribe el audio Y lo estructura directamente como JSON
        en un solo paso.
        """
        # 1. Modificamos el prompt base (que era para imágenes) para que 
        # las instrucciones tengan sentido para un archivo de audio.
        prompt_audio = (
            EXTRACTION_PROMPT.replace(
                "Analiza la imagen proporcionada que contiene una nota de enfermería escrita a mano.",
                "Escucha el audio proporcionado en el que una enfermera dicta una nota clínica. "
                "Transcribe lo que escuchas y extrae la información estructurada."
            ).replace(
                "\"raw_text\": \"transcripción literal de todo el texto que ves en la imagen\"",
                "\"raw_text\": \"transcripción literal de todo lo que escuchas en el audio\""
            ).replace(
                "Si la nota es ilegible en alguna parte, escríbelo en 'observations'.",
                "Si alguna parte del audio es inaudible o poco clara, escríbelo en 'observations'."
            )
        )

        # 2. Importamos la librería base64 estándar de Python
        import base64
        
        # 3. Convertimos los bytes crudos del audio a una cadena codificada en Base64.
        # Esto es necesario porque la API de Google espera que los archivos binarios
        # se envíen como texto codificado cuando se envían "inline" (dentro de la petición).
        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

        # 4. Usamos la Interactions API de Gemini (la interfaz más moderna del SDK).
        # client.interactions.create() permite enviar múltiples tipos de datos fácilmente.
        respuesta = self.client.interactions.create(
            model="gemini-3.7-flash",  # Usamos el modelo 3.7 Flash que tiene soporte multimodal (audio) activo
            input=[
                # Primer elemento del input: El texto con las instrucciones (prompt)
                {
                    "type": "text",
                    "text": prompt_audio,
                },
                # Segundo elemento del input: El archivo de audio
                {
                    "type": "audio",
                    "data": audio_base64,       # Los datos del audio en base64
                    "mime_type": mime_type,     # El formato (ej. "audio/wav")
                },
            ]
        )

        # 5. La Interactions API devuelve la respuesta textual en el atributo 'output_text'.
        # Usamos .strip() para limpiar espacios en blanco al inicio y al final.
        texto_respuesta = respuesta.output_text.strip()

        # 6. Limpieza de marcadores Markdown. Si el modelo devuelve el JSON
        # envuelto en ```json ... ```, este bloque lo recorta para dejar solo las llaves { }.
        if texto_respuesta.startswith("```"):
            lineas = texto_respuesta.split("\n")
            inicio = next(
                (i for i, l in enumerate(lineas) if l.strip().startswith("{")), 1
            )
            fin = next(
                (i for i in range(len(lineas)-1, -1, -1) if lineas[i].strip().endswith("}")),
                len(lineas)-1
            )
            texto_respuesta = "\n".join(lineas[inicio:fin+1])

        # 7. Convertimos el texto (String) a un diccionario de Python (Dict).
        try:
            datos = json.loads(texto_respuesta)
        except json.JSONDecodeError as e:
            # Si Gemini se equivoca y no devuelve un JSON válido, lanzamos un error claro.
            raise ValueError(
                f"Gemini no devolvió JSON válido desde el audio.\n"
                f"Error: {e}\nRespuesta recibida:\n{texto_respuesta}"
            )

        # 8. Agregamos metadata (datos sobre los datos) para saber de dónde salió esta nota.
        # Útil para auditorías en el historial médico.
        datos["_metadata"] = {
            "processed_at": datetime.datetime.now().isoformat(),  # Fecha y hora actual
            "model_used": "gemini-3.7-flash",                     # Modelo utilizado
            "source_image": "audio_input",                        # Indicador de que fue voz
            "input_type": "audio",                                # Tipo de entrada
            "audio_mime_type": mime_type,                         # Formato del archivo subido
        }

        # 9. Retornamos el diccionario completo, listo para pasar a OKF y PDF.
        return datos
