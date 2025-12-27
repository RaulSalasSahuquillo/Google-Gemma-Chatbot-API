from google import genai
from dotenv import load_dotenv
import os
import sqlite3
import hashlib
from flask import Flask, render_template, request, render_template_string, flash, redirect, url_for, session
import time

# Acabo de descubrir esta manera de hacer html y me da pereza hacer archivos aparte XD. Por cierto, el CSS me lo ha hecho Antigravity.
index_template = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EN.AI - ENEI PROJECT</title>
    <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Playfair+Display:ital,wght@0,400;1,700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-black: #050505;
            --smoke-light: rgba(200, 200, 200, 0.15);
            --glow-text: rgba(255, 255, 255, 0.8);
            --panel-alpha: rgba(10, 10, 10, 0.7);
        }

        body {
            background-color: var(--bg-black);
            /* Fondo con gradiente radial para simular profundidad y humo */
            background: radial-gradient(circle at center, #1a1a1a 0%, #000 100%);
            color: #d4d4d4;
            font-family: 'Playfair Display', serif;
            margin: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            overflow: hidden;
        }

        /* Capa de humo animada (Efecto visual) */
        body::before {
            content: "";
            position: absolute;
            width: 200%; height: 200%;
            background: url('https://www.transparenttextures.com/patterns/asfalt-dark.png');
            opacity: 0.2;
            animation: moveSmoke 60s linear infinite;
            pointer-events: none;
        }

        @keyframes moveSmoke {
            from { transform: translate(-10%, -10%); }
            to { transform: translate(0%, 0%); }
        }

        .container {
            width: 95%;
            max-width: 900px;
            height: 90vh;
            background: var(--panel-alpha);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.05);
            display: flex;
            flex-direction: column;
            position: relative;
            box-shadow: 0 0 50px rgba(0,0,0,1);
            z-index: 1;
        }

        .chat-header {
            padding: 40px 20px;
            text-align: center;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        .chat-header h1 {
            font-family: 'Cinzel', serif;
            font-size: 2.5rem;
            margin: 0;
            letter-spacing: 8px;
            color: #fff;
            text-shadow: 0 0 15px var(--glow-text), 2px 2px 10px rgba(0,0,0,0.5);
            text-transform: uppercase;
        }

        .chat-header p {
            font-family: 'Cinzel', serif;
            font-size: 0.7rem;
            letter-spacing: 4px;
            opacity: 0.5;
            margin-top: 10px;
        }

        .chat-box {
            flex: 1;
            overflow-y: auto;
            padding: 30px;
            display: flex;
            flex-direction: column;
            gap: 25px;
            mask-image: linear-gradient(to bottom, transparent, black 10%, black 90%, transparent);
        }

        .msg {
            max-width: 70%;
            padding: 15px 25px;
            position: relative;
            font-size: 1.05rem;
            animation: fadeIn 0.8s ease-in-out;
            border-left: 1px solid rgba(255,255,255,0.1);
        }

        @keyframes fadeIn { from { opacity: 0; filter: blur(5px); } to { opacity: 1; filter: blur(0); } }

        .autor {
            display: block;
            font-family: 'Cinzel', serif;
            font-size: 0.6rem;
            margin-bottom: 8px;
            letter-spacing: 2px;
            color: var(--primary-neon);
            opacity: 0.6;
        }

        .user {
            align-self: flex-end;
            text-align: right;
            border-left: none;
            border-right: 1px solid rgba(255,255,255,0.2);
            background: linear-gradient(to left, rgba(255,255,255,0.03), transparent);
        }

        .ai {
            align-self: flex-start;
            background: linear-gradient(to right, rgba(255,255,255,0.03), transparent);
        }

        .input-form {
            padding: 30px;
            display: flex;
            background: rgba(0, 0, 0, 0.4);
            border-top: 1px solid rgba(255, 255, 255, 0.05);
        }

        input[type="text"] {
            flex: 1;
            background: transparent;
            border: none;
            border-bottom: 1px solid rgba(255, 255, 255, 0.2);
            padding: 10px;
            color: #fff;
            font-family: 'Playfair Display', serif;
            font-size: 1.2rem;
            outline: none;
            transition: 0.4s;
        }

        input[type="text"]:focus {
            border-bottom-color: #fff;
            text-shadow: 0 0 5px var(--glow-text);
        }

        button {
            background: transparent;
            border: 1px solid rgba(255, 255, 255, 0.3);
            color: #fff;
            padding: 0 30px;
            margin-left: 20px;
            font-family: 'Cinzel', serif;
            cursor: pointer;
            transition: 0.3s;
            letter-spacing: 2px;
        }

        button:hover {
            background: #fff;
            color: #000;
            box-shadow: 0 0 20px #fff;
        }

        .logout-btn {
            position: absolute;
            top: 20px; right: 20px;
            color: rgba(255,255,255,0.3);
            text-decoration: none;
            font-family: 'Cinzel', serif;
            font-size: 0.6rem;
            letter-spacing: 2px;
            transition: 0.3s;
        }

        .logout-btn:hover { color: #fff; }

        /* Scrollbar invisible */
        .chat-box::-webkit-scrollbar { width: 3px; }
        .chat-box::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); }
    </style>
</head>
<body>

<div class="container">
    <a href="{{ url_for('logout') }}" class="logout-btn">TERMINAR SESIÓN</a>
    
    <div class="chat-header">
        <h1>EN.AI</h1>
        <p>ENEI PROJECT // OPERADOR: {{ user }}</p>
    </div>

    <div class="chat-box" id="chatBox">
        {% for msg in chat %}
            <div class="msg {% if msg.autor == 'Tú' %}user{% else %}ai{% endif %}">
                <span class="autor">{{ msg.autor }}</span>
                {{ msg.texto }}
            </div>
        {% endfor %}
    </div>

    <form method="POST" class="input-form">
        <input type="text" name="mensaje" placeholder="Escribe al sistema..." required autofocus autocomplete="off">
        <button type="submit">ENVIAR</button>
    </form>
</div>

<script>
    const cb = document.getElementById('chatBox');
    cb.scrollTop = cb.scrollHeight;
</script>

</body>
</html>
"""

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
            "system_instruction": "Eres EN.AI, una IA desarrollada por el estudio personal de ENEI PROJECT que pertenece al desarrollador Raúl Salas Sahuquillo. Responde de manera útil, amigable y profesional. Habla en español.",
            "tools": [{"google_search": {}}], # Herramienta para Google Serch
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

# HTML simple para login y registro
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

# RUTAS

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
            try:                          # Lol, no sabía que iba ya por la línea 300
                response = chat_session.send_message(user_message)
                historial.append({"autor": "Tú", "texto": user_message})
                historial.append({"autor": "EN.AI", "texto": response.text})
            except Exception as e:
                if "429" in str(e): # El error 429 indica límite de tokens. Cuando aparece toca cambiar de api key.
                    error_msg = "Límite de tasa alcanzado. Por favor, espera un momento antes de continuar."
                else:
                    error_msg = f"Ocurrió un error inesperado: {e}"
                historial.append({"autor": "Sistema", "texto": f"Error: {e}"})
        return render_template_string(index_template, chat=historial, user=session["username"])
    
    # Si es GET (Recarga), reiniciamos el chat
    historial = []
    chat_session = crear_chat()
    return render_template_string(index_template, chat=historial, user=session["username"])

# Ruta para cerrar sesión
@app.route('/logout')
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)