@echo off
cd /d "%~dp0"
echo ======================================
echo Traductor ES->DA - Version Simple
echo ======================================
echo.
echo Iniciando servidor...
echo.
venv\Scripts\python.exe app_simple.py
echo.
echo Servidor detenido.
pause
