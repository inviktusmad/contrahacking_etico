from flask import Flask, request, redirect
import datetime
import os

app = Flask(__name__)

# --- CONFIGURACIÓN DEL LOCALIZADOR DE BPOST ---
# Este es el número de seguimiento que quieres que se muestre en la página de Bpost.
TRACKING_NUMBER = "CE539544965BE"

# --- CONFIGURACIÓN DE LA URL DE REDIRECCIÓN ---
# La URL base a la que el estafador será redirigido
REDIRECT_BASE_URL = "https://track.bpost.cloud/btr/web/#/search"

# --- CONFIGURACIÓN DEL ARCHIVO DE LOG ---
# El archivo access.log se creará en el mismo directorio donde tengas tu app.py
LOG_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'access.log')

# --- RUTA PRINCIPAL DEL SERVIDOR WEB ---
# Esta es la función que se ejecuta cada vez que alguien accede a la URL principal (http://tu_ip:8081/)
@app.route('/')
def index():
    # Obtener la dirección IP del visitante.
    # Priorizamos X-Forwarded-For para obtener la IP real detrás de Serveo o cualquier otro proxy.
    visitor_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    # Obtener la información del navegador del visitante (User-Agent).
    user_agent = request.headers.get('User-Agent')
    # Obtener la fecha y hora exacta de la visita.
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Crear la entrada del log
    log_entry = f"[{timestamp}] IP: {visitor_ip} | User-Agent: {user_agent}\n"

    # Escribir la entrada en el archivo de log
    try:
        with open(LOG_FILE_PATH, 'a') as f:
            f.write(log_entry)
        print(f"Log registrado: {log_entry.strip()}") # Para ver en la consola que funciona
    except Exception as e:
        print(f"ERROR al escribir en el log: {e}")

    # Construir la URL de redirección final con el número de seguimiento
    final_redirect_url = f"{REDIRECT_BASE_URL}?itemCode={TRACKING_NUMBER}&lang=nl"

    # Redirigir al estafador a la URL de Bpost configurada
    return redirect(final_redirect_url, code=302)

if __name__ == '__main__':
    # Asegúrate de que Flask escuche en 0.0.0.0 para que sea accesible desde Serveo
    # y en el puerto 8081 como lo hemos estado usando.
    app.run(host='0.0.0.0', port=8081)

