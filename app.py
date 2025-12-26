from google import genai
from dotenv import load_dotenv
import os

load_dotenv() # Carga las variables de entorno desde el archivo .env

# Introduce la IA en la terminal
print("EN.AI, powered by Gemini, developed by Raúl Salas Sahuquillo")

# Inicializa el cliente con la clave API
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("ERROR: La clave API no es válida o no está configurada. Por favor, consisidera crear un archivo .env con GEMINI_API_KEY=tu_clave_aquí.")
    exit()
client = genai.Client(api_key=api_key) # Se usa os para ocultar la clave API

# Definimos el modelo de Gemini y su base de configuración al responder
chat = client.chats.create(
    model = "gemini-2.5-flash", # Modelo de Gemini más avanzado disponible como API
    config = {
        "system_instruction": "Eres EN.AI, una IA desarrollada por el estudio personal de ENEI PROJECT que pertenece al desarrollador Raúl Salas Sahuquillo. Responde de manera útil, amigable y profesional. Habla en español.",
        "tools": [{"google_search": {}}], # Habilita la herramienta de búsqueda en Google
    }
)

# Bucle principal para interactuar con la IA
while True:
    user_input = input("Escribe tu pregunta: ") # Entrada del usuario
    # Condición para salir del chat
    if user_input.lower().strip() in ["exit", "adiós", "salir", "adios", "bye"]:
        print("Fin del chat.")
        break
    if not user_input:
        continue
    # Envía el mensaje del usuario a la IA y obtiene la respuesta
    try:
        response = chat.send_message(user_input)
        print("EN.AI:", response.text) # Muestra la respuesta de la IA
    except Exception as e:
        print(f"Ocurrió un error al comunicarse con la API de Gemini: {e}")