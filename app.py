from google import genai
from dotenv import load_dotenv
import os
import sqlite3
import hashlib
from flask import Flask, render_template, request, render_template_string, flash, redirect, url_for, session
import time

index_template = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EN.AI - Quantum Interface</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@300;500;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary-neon: #00f2ff;
            --secondary-neon: #7000ff;
            --bg-dark: #060b13;
            --glass: rgba(255, 255, 255, 0.05);
            --glass-border: rgba(255, 255, 255, 0.1);
        }

        body {
            background: radial-gradient(circle at center, #101a26 0%, var(--bg-dark) 100%);
            color: #e0e0e0;
            font-family: 'Rajdhani', sans-serif;
            margin: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            overflow: hidden;
        }

        .container {
            width: 90%;
            max-width: 850px;
            height: 85vh;
            background: var(--glass);
            backdrop-filter: blur(15px);
            border: 1px solid var(--glass-border);
            border-radius: 20px;
            display: flex;
            flex-direction: column;
            box-shadow: 0 0 40px rgba(0, 0, 0, 0.5), inset 0 0 20px rgba(0, 242, 255, 0.05);
            position: relative;
        }

        /* Efecto de línea de escaneo superior */
        .container::before {
            content: "";
            position: absolute;
            top: 0; left: 0; width: 100%; height: 2px;
            background: linear-gradient(90deg, transparent, var(--primary-neon), transparent);
            animation: scan 3s linear infinite;
        }

        @keyframes scan { 0% { left: -100%; } 100% { left: 100%; } }

        .chat-header {
            padding: 20px;
            text-align: center;
            border-bottom: 1px solid var(--glass-border);
            background: rgba(0, 0, 0, 0.2);
        }

        .chat-header h1 {
            margin: 0;
            font-family: 'Orbitron', sans-serif;
            font-size: 1.5rem;
            letter-spacing: 4px;
            color: var(--primary-neon);
            text-shadow: 0 0 10px var(--primary-neon);
        }

        .chat-header p { margin: 5px 0 0; font-size: 0.8rem; opacity: 0.6; text-transform: uppercase; }

        .chat-box {
            flex: 1;
            overflow-y: auto;
            padding: 25px;
            display: flex;
            flex-direction: column;
            gap: 20px;
            scrollbar-width: thin;
            scrollbar-color: var(--primary-neon) transparent;
        }

        /* Estilo de los mensajes */
        .msg {
            max-width: 75%;
            padding: 15px 20px;
            border-radius: 15px;
            position: relative;
            font-size: 1.1rem;
            animation: fadeIn 0.4s ease-out;
            line-height: 1.4;
        }

        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

        .user {
            align-self: flex-end;
            background: linear-gradient(135deg, var(--secondary-neon), #4a00e0);
            color: white;
            border-bottom-right-radius: 2px;
            box-shadow: 0 4px 15px rgba(112, 0, 255, 0.3);
        }

        .ai {
            align-self: flex-start;
            background: rgba(255, 255, 255, 0.07);
            border: 1px solid var(--glass-border);
            color: #fff;
            border-bottom-left-radius: 2px;
        }

        .autor {
            display: block;
            font-family: 'Orbitron', sans-serif;
            font-size: 0.65rem;
            margin-bottom: 5px;
            text-transform: uppercase;
            letter-spacing: 1px;
            opacity: 0.8;
        }

        .input-form {
            padding: 20px;
            background: rgba(0, 0, 0, 0.3);
            display: flex;
            gap: 15px;
            border-top: 1px solid var(--glass-border);
        }

        input[type="text"] {
            flex: 1;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--glass-border);
            padding: 15px;
            color: white;
            border-radius: 10px;
            outline: none;
            transition: 0.3s;
            font-family: 'Rajdhani', sans-serif;
            font-size: 1.1rem;
        }

        input[type="text"]:focus {
            border-color: var(--primary-neon);
            box-shadow: 0 0 10px rgba(0, 242, 255, 0.2);
        }

        button {
            background: transparent;
            border: 1px solid var(--primary-neon);
            color: var(--primary-neon);
            padding: 0 25px;
            border-radius: 10px;
            cursor: pointer;
            font-family: 'Orbitron', sans-serif;
            font-size: 0.8rem;
            text-transform: uppercase;
            transition: 0.3s;
        }

        button:hover {
            background: var(--primary-neon);
            color: var(--bg-dark);
            box-shadow: 0 0 20px var(--primary-neon);
        }

        .logout-btn {
            position: absolute;
            top: 20px;
            right: 20px;
            color: #ff4b2b;
            text-decoration: none;
            font-size: 0.8rem;
            border: 1px solid #ff4b2b;
            padding: 5px 10px;
            border-radius: 5px;
        }

        /* Scrollbar Tuneada */
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-thumb { background: var(--primary-neon); border-radius: 10px; }
    </style>
</head>
<body>

<div class="container">
    <a href="{{ url_for('logout') }}" class="logout-btn">DISCONNECT</a>
    
    <div class="chat-header">
        <h1>EN.AI</h1>
        <p>ENEI PROJECT // SYST_OP: {{ user }}</p>
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
        <input type="text" name="mensaje" placeholder="Awaiting input command..." required autofocus autocomplete="off">
        <button type="submit">Execute</button>
    </form>
</div>

<script>
    // Auto-scroll al final del chat al cargar
    const chatBox = document.getElementById('chatBox');
    chatBox.scrollTop = chatBox.scrollHeight;
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
                if "429" in str(e): # El error 429 indica límite de tokens. Cuando aparece toca cambiar de api key.
                    error_msg = "Límite de tasa alcanzado. Por favor, espera un momento antes de continuar."
                else:
                    error_msg = f"Ocurrió un error inesperado: {e}"
                historial.append({"autor": "Sistema", "texto": f"Error: {e}"})
        return render_template_string(index_template, chat=historial, user=session["username"])
    
    # Si es GET (Recarga), reiniciamos el chat como pediste antes
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