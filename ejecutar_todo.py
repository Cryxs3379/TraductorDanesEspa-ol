#!/usr/bin/env python3
"""
Script para ejecutar todo: iniciar servidor, esperar, ejecutar test.
"""
import subprocess
import sys
import time
import requests
import threading
import os

def iniciar_servidor():
    """Iniciar el servidor en un proceso separado."""
    try:
        # Usar el path relativo al script actual
        script_dir = os.path.dirname(os.path.abspath(__file__))
        server_script = os.path.join(script_dir, 'start_server.py')
        
        # Encontrar python del venv
        venv_python = os.path.join(script_dir, 'venv', 'Scripts', 'python.exe')
        if os.path.exists(venv_python):
            python_exe = venv_python
        else:
            python_exe = sys.executable
        
        print("Iniciando servidor...")
        process = subprocess.Popen([python_exe, server_script], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE,
                                 cwd=script_dir)
        return process
    except Exception as e:
        print(f"Error iniciando servidor: {e}")
        return None

def verificar_servidor(max_attempts=30):
    """Verificar que el servidor esté funcionando."""
    for i in range(max_attempts):
        try:
            response = requests.get('http://localhost:8000/health', timeout=3)
            if response.status_code == 200:
                data = response.json()
                modelo_ok = data.get('model_loaded', False)
                print(f"Servidor OK - Modelo: {'Cargado' if modelo_ok else 'No cargado'}")
                return modelo_ok
        except:
            pass
        
        if i < max_attempts - 1:
            print(f"Esperando servidor... intento {i+1}/{max_attempts}")
            time.sleep(2)
    
    print("Timeout esperando al servidor")
    return False

def ejecutar_test():
    """Ejecutar el test."""
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        test_script = os.path.join(script_dir, 'test_final_completo_no_emoji.py')
        venv_python = os.path.join(script_dir, 'venv', 'Scripts', 'python.exe')
        
        if os.path.exists(venv_python):
            python_exe = venv_python
        else:
            python_exe = sys.executable
        
        print("\nEjecutando test...")
        result = subprocess.run([python_exe, test_script], 
                              capture_output=True, text=True, timeout=120, cwd=script_dir)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"Error ejecutando test: {e}")
        return False

if __name__ == "__main__":
    print("EJECUTANDO PROCESO COMPLETO")
    print("=" * 50)
    
    # Iniciar servidor
    server_process = iniciar_servidor()
    if not server_process:
        print("No se pudo iniciar el servidor")
        sys.exit(1)
    
    try:
        # Esperar a que el servidor esté listo
        if not verificar_servidor():
            print("El servidor no respondió en el tiempo esperado")
            server_process.terminate()
            sys.exit(1)
        
        # Ejecutar test
        if ejecutar_test():
            print("\nRESULTADO: TEST EXITOSO!")
        else:
            print("\nRESULTADO: TEST FALLÓ")
            
    finally:
        # Limpiar proceso del servidor
        if server_process:
            print("\nCerrando servidor...")
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()
