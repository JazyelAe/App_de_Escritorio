@echo off
title DeskData Pro - Instalador y Ejecutor Local (Python + PySide6)
echo ===============================================================
echo   Iniciando Aplicacion de Escritorio DeskData Pro (Offline)
echo ===============================================================
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no esta instalado en el sistema.
    pause
    exit /b 1
)
if not exist ".venv" (
    echo [1/3] Creando entorno virtual local...
    python -m venv .venv
)
call .venv\Scripts\activate.bat
echo [2/3] Verificando dependencias locales (PySide6)...
pip install -r requirements.txt
echo [3/3] Ejecutando aplicacion de escritorio...
python main.py
pause
