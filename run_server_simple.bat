@echo off
cd /d "%~dp0"
echo ======================================
echo Iniciando servidor de traducción
echo ======================================
set MODEL_DIR=./models/nllb-600m
set CT2_DIR=./models/nllb-600m-ct2-int8
echo.
echo Modelo: %MODEL_DIR%
echo CT2: %CT2_DIR%
echo.
venv\Scripts\python.exe -m uvicorn app.app:app --host 0.0.0.0 --port 8000
pause

