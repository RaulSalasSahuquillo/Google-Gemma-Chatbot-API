from google import genai
from dotenv import load_dotenv
import os

load_dotenv() # Carga las variables de entorno desde el archivo .env

print("EN.AI, powered by Gemini, developed by Raúl Salas Sahuquillo")

# Inicializa el cliente con la clave API
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) # Se usa os para ocultar la clave API

response = client.models.generate_content(
    model="gemini-2.5-flash", contents="Hola" # Model para modelo de Gemini y el prompt es contents
)
print(response.text)