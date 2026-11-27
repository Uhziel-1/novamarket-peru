@echo off
title NovaMarket Peru - Reentrenamiento CRISP-DM Completo
cd /d "%~dp0"
echo [1/3] Extraccion y auditoria de dataset...
".venv\Scripts\python.exe" src\extract_data.py
echo [2/3] Analisis exploratorio y graficas EDA...
".venv\Scripts\python.exe" src\eda.py
echo [3/3] Entrenamiento K-Means RFM, Reglas de Asociacion y Predictor Recompra + SHAP...
".venv\Scripts\python.exe" src\train.py
echo.
echo Pipeline CRISP-DM completado.
pause
