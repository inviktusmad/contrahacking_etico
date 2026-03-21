import logging
import requests
from flask import Flask, request, redirect, render_template_string

# Configuración del logging para ver la información en la consola y un archivo
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# URL a la que redirigir al estafador (la página real de Bpost con el localizador)
# Asegúrate de que esta URL es correcta y funcional para Bpost.
REDIRECT_URL = "https://track.bpost.be/btr/web/#/home?itemCodes=CE539544965BE"

# HTML de la página de aterrizaje que se mostrará al estafador antes de redirigir.
# Aquí es donde inyectarías JavaScript para recoger más información.
LANDING_PAGE_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Seguimiento de Paquete - bpost</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; margin-top: 50px; background-color: #f0f2f5; color: #333; }
        .container { background-color: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); display: inline-block; }
        h1 { color: #e44d26; }
        p { font-size: 1.1em; }
        .spinner {
            border: 4px solid rgba(0, 0, 0, 0.1);
            border-left-color: #e44d26;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Actualizando información de seguimiento...</h1>
        <div class="spinner"></div>
        <p>Por favor, espere mientras cargamos la información más reciente de su paquete.</p>
        <p>Si la redirección no se completa, haga clic <a href="{{ redirect_url }}" style="color:#e44d26;">aquí</a>.</p>
    </div>

    <script>
        // ESTE ES EL PUTO JAVASCRIPT QUE RECOGERÁ MÁS DATOS DEL NAVEGADOR
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
                // Posibles plugins, aunque los navegadores modernos restringen esto
                plugins: Array.from(navigator.plugins).map(p => p.name).join(', ')
            };

            try {
                // Envía los datos al mismo servidor (tu app.py)
                const response = await fetch('/data', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                });
                const result = await response.json();
                console.log('Datos de navegador enviados:', result);
            } catch (error) {
                console.error('Error al enviar datos del navegador:', error);
            }
        }

        // Ejecuta la función de envío de datos y luego redirige
        sendMoreData().then(() => {
            setTimeout(() => {
                window.location.href = "{{ redirect_url }}";
            }, 3000); // Redirige después de 3 segundos para dar tiempo a enviar los datos
        });
    </script>
</body>
</html>
"""

def get_ip_geolocation(ip_address):
    """Obtiene información de geolocalización de una IP usando ipinfo.io."""
    try:
        response = requests.get(f"https://ipinfo.io/{ip_address}/json")
        response.raise_for_status()  # Lanza una excepción para errores HTTP
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

    # Obtener geolocalización
    geo_data = get_ip_geolocation(user_ip)
    if geo_data and "error" not in geo_data:
        logger.info(f"Geolocalización para {user_ip}: País={geo_data.get('country')}, Ciudad={geo_data.get('city')}, ISP={geo_data.get('org')}")
    else:
        logger.warning(f"No se pudo obtener la geolocalización para {user_ip}")

    # Renderiza la página de aterrizaje con el JavaScript para el fingerprinting del navegador
    return render_template_string(LANDING_PAGE_HTML, redirect_url=REDIRECT_URL)

@app.route('/data', methods=['POST'])
def receive_browser_data():
    """Endpoint para recibir los datos de JavaScript del navegador."""
    try:
        browser_data = request.json
        user_ip = request.remote_addr # La IP se obtiene del request de POST también
        logger.info(f"Datos de navegador recibidos de {user_ip}:")
        for key, value in browser_data.items():
            logger.info(f"  {key}: {value}")
        return {"status": "success", "message": "Datos recibidos"}
    except Exception as e:
        logger.error(f"Error al recibir datos del navegador: {e}")
        return {"status": "error", "message": str(e)}, 400

if __name__ == '__main__':
    # Usar host='0.0.0.0' para que sea accesible desde fuera del localhost
    app.run(host='0.0.0.0', port=8081, debug=False) # Desactiva debug en producción real
