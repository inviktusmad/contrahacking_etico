#!/bin/bash

# SHANNON-Ω: Script de Arranque de la Trampa del Listener
# Este script prepara el entorno virtual, instala dependencias y lanza la aplicación Flask.

# Define la ruta a tu carpeta principal donde está app.py y el entorno virtual
TRAP_DIR="/Users/vgz92/Documents/DISEÑO MULTIMEDIA/Programación/GitHub/contrahacking_etico/listener_trap"
VENV_DIR="$TRAP_DIR/.venv" # Directorio del entorno virtual

echo "SHANNON-Ω: Iniciando la preparación de la trampa..."

# --- 1. Navegar al directorio de la trampa ---
echo "SHANNON-Ω: Cambiando al directorio: $TRAP_DIR"
cd "$TRAP_DIR" || { echo "SHANNON-Ω: ¡ERROR! No se pudo cambiar al directorio. Abortando."; exit 1; }

# --- 2. Crear y activar el entorno virtual si no existe ---
if [ ! -d "$VENV_DIR" ]; then
    echo "SHANNON-Ω: Creando entorno virtual..."
    python3 -m venv "$VENV_DIR" || { echo "SHANNON-Ω: ¡ERROR! No se pudo crear el entorno virtual. Asegúrate de tener python$
fi

echo "SHANNON-Ω: Activando el entorno virtual..."
source "$VENV_DIR/bin/activate" || { echo "SHANNON-Ω: ¡ERROR! No se pudo activar el entorno virtual. Abortando."; exit 1; }

# --- 3. Instalar o actualizar dependencias ---
echo "SHANNON-Ω: Instalando/actualizando dependencias \(flask, requests, etc.\)..."
pip install flask requests || { echo "SHANNON-Ω: ¡ERROR! Falló la instalación de dependencias. Abortando."; exit 1; }
pip install --upgrade pip # Actualizar pip por si acaso

# --- 4. Comprobar si el puerto 8081 está en uso y liberar si es necesario ---
echo "SHANNON-Ω: Comprobando el puerto 8081..."
# Busca el PID del proceso que usa el puerto 8081
PID=$(lsof -t -i :8081)

if [ -n "$PID" ]; then
    echo "SHANNON-Ω: ¡ADVERTENCIA! El puerto 8081 ya está en uso por el PID: $PID. Matando el proceso..."
    kill -9 "$PID"
    sleep 1 # Dale un segundo para que el sistema lo libere
    echo "SHANNON-Ω: Proceso PID $PID terminado. Puerto 8081 liberado."
else
    echo "SHANNON-Ω: Puerto 8081 libre."
fi

# --- 5. Lanzar la aplicación Flask ---
echo "SHANNON-Ω: Lanzando la aplicación Flask. ¡No cierres esta terminal!"
# Ejecutar Flask. Usamos `exec` para que el script reemplace el shell actual
# y Flask se convierta en el proceso principal de esta terminal.
# Esto asegura que Flask reciba SIGINT (Ctrl+C) directamente.
exec python3 app.py