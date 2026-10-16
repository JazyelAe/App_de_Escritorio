#!/usr/bin/env bash
set -e
echo "==============================================================="
echo "  Iniciando Aplicación de Escritorio DeskData Pro (Offline)"
echo "==============================================================="
if [ ! -d ".venv" ]; then
    echo "[1/3] Creando entorno virtual local..."
    python3 -m venv .venv
fi
source .venv/bin/activate
echo "[2/3] Instalando dependencias (PySide6)..."
pip install -r requirements.txt
echo "[3/3] Ejecutando aplicación de escritorio..."
python3 main.py
