@echo off
title NovaMarket Peru - Sistema Web + ML
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] No se encontro .venv\Scripts\python.exe. Crea el entorno e instala requirements.txt.
    pause
    exit /b 1
)
echo Iniciando NovaMarket Peru (Web + Backend) en http://127.0.0.1:38420 ...
".venv\Scripts\python.exe" run_local.py
pause
