from flask import Flask, request, redirect
from datetime import datetime
import os

app = Flask(__name__)

# El archivo de log se creará dentro de /Users/vgz92/Downloads/listener_trap/
LOG_FILE = "access.log"
# La URL a la que redirigir al estafador para que no sospeche.
REDIRECT_URL = "https://www.google.com" 

@app.route("/", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
def index():
    user_agent = request.headers.get("User-Agent", "unknown")
    ip_address = request.headers.get("X-Forwarded-For", request.remote_addr or "unknown")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] IP: {ip_address} | User-Agent: {user_agent}\n"
    
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        print(f"ERROR: No se pudo escribir en el archivo de log '{LOG_FILE}': {e}")
    
    return redirect(REDIRECT_URL)

if __name__ == "__main__":
    print(f"")
    print(f"-------------------------------------------------------")
    print(f"[*] ¡Servidor Flask de rastreo iniciado en tu Mac!")
    print(f"[*] Escuchando en **TODAS** las IPs de tu Mac (0.0.0.0) en el puerto: 5000")
    print(f"[*] Los datos se registrarán en el archivo: '{os.path.abspath(LOG_FILE)}'")
    print(f"[*] Después de registrar, se redirigirá al visitante a: '{REDIRECT_URL}'")
    print(f"[*] Para detener este servidor, presiona: Ctrl + C")
    print(f"-------------------------------------------------------")
    print(f"")
    app.run(host='0.0.0.0', port=5000, debug=False)

