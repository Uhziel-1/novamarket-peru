@echo off
title NovaMarket Peru - Pruebas Automatizadas
cd /d "%~dp0"
echo Ejecutando suite pytest...
".venv\Scripts\python.exe" -m pytest tests\test_api.py -v
echo.
pause
