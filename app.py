from google import genai
from dotenv import load_dotenv
import os
import sqlite3
import hashlib
from flask import Flask, render_template, request, render_template_string, flash, redirect, url_for, session
import time

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24) # Clave para las sesiones

# --- CONFIGURACIÓN DE IA ---
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    exit("Error: GEMINI_API_KEY no encontrada.")

client = genai.Client(api_key=api_key)

# Función para crear una nueva sesión de chat
def crear_chat():
    return client.chats.create(
        model="gemini-2.5-flash", 
        config={
            "system_instruction": "Eres EN.AI, desarrollado por Raúl Salas Sahuquillo. Responde amigablemente en español.",
            "tools": [{"google_search": {}}],
        }
    )

# Inicializamos el chat globalmente (o por sesión)
chat_session = crear_chat()
historial = []

# --- BASE DE DATOS ---
def init_db():
    with sqlite3.connect("users.db") as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)

init_db() # Llamamos a la función al arrancar

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# --- PLANTILLAS HTML (Incrustadas para el ejemplo) ---
login_template = """
<!DOCTYPE html>
<html>
<head><title>Login - EN.AI</title></head>
<body>
    <h2>Iniciar Sesión</h2>
    <form method="POST">
        Usuario: <input type="text" name="username" required><br>
        Contraseña: <input type="password" name="password" required><br>
        <button type="submit">Entrar</button>
    </form>
    <p><a href="{{ url_for('register') }}">Registrarse</a></p>
    {% with messages = get_flashed_messages() %}{% if messages %}
        <ul>{% for msg in messages %}<li>{{ msg }}</li>{% endfor %}</ul>
    {% endif %}{% endwith %}
</body>
</html>
"""

register_template = """
<!DOCTYPE html>
<html>
<head><title>Registro - EN.AI</title></head>
<body>
    <h2>Registro de Usuario</h2>
    <form method="POST">
        Usuario: <input type="text" name="username" required><br>
        Contraseña: <input type="password" name="password" required><br>
        <button type="submit">Registrar</button>
    </form>
    <p><a href="{{ url_for('login') }}">Volver al login</a></p>
    {% with messages = get_flashed_messages() %}{% if messages %}
        <ul>{% for msg in messages %}<li>{{ msg }}</li>{% endfor %}</ul>
    {% endif %}{% endwith %}
</body>
</html>
"""

# --- RUTAS ---

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = hash_password(request.form["password"])

        with sqlite3.connect("users.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
            user = cursor.fetchone()

        if user:
            session["username"] = username
            return redirect(url_for("home"))
        else:
            flash("Usuario o contraseña incorrectos.")
    return render_template_string(login_template)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = hash_password(request.form["password"])
        try:
            with sqlite3.connect("users.db") as conn:
                conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            flash("Registro éxito. Inicia sesión.")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("El nombre de usuario ya existe.")
    return render_template_string(register_template)

@app.route('/', methods=['GET', 'POST'])
def home():
    global chat_session, historial
    
    # Si no hay usuario en sesión, mandarlo al login
    if "username" not in session:
        return redirect(url_for("login"))

    if request.method == 'POST':
        user_message = request.form.get("mensaje")
        if user_message:
            try:
                response = chat_session.send_message(user_message)
                historial.append({"autor": "Tú", "texto": user_message})
                historial.append({"autor": "EN.AI", "texto": response.text})
            except Exception as e:
                if "429" in str(e):
                    error_msg = "Límite de tasa alcanzado. Por favor, espera un momento antes de continuar."
                else:
                    error_msg = f"Ocurrió un error inesperado: {e}"
                historial.append({"autor": "Sistema", "texto": f"Error: {e}"})
        return render_template('index.html', chat=historial, user=session["username"])
    
    # Si es GET (Recarga), reiniciamos el chat como pediste antes
    historial = []
    chat_session = crear_chat()
    return render_template('index.html', chat=historial, user=session["username"])

@app.route('/logout')
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)