#!/usr/bin/env python3
"""
Script para ejecutar el test en loop hasta que funcione.
"""
import subprocess
import sys
import time
import requests

def verificar_servidor():
    """Verificar que el servidor esté funcionando."""
    try:
        response = requests.get('http://localhost:8000/health', timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get('model_loaded', False)
        return False
    except:
        return False

def ejecutar_test():
    """Ejecutar el test."""
    try:
        result = subprocess.run([sys.executable, 'test_final_completo.py'], 
                              capture_output=True, text=True, timeout=60)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "Timeout", "Test tardó demasiado"
    except Exception as e:
        return False, "", str(e)

if __name__ == "__main__":
    print("🔄 EJECUTANDO TEST EN LOOP")
    print("=" * 50)
    
    max_intentos = 5
    intento = 1
    
    while intento <= max_intentos:
        print(f"\n🎯 Intento {intento}/{max_intentos}")
        
        # Verificar servidor
        if not verificar_servidor():
            print("❌ Servidor no disponible")
            print("💡 Asegúrate de ejecutar: python start_server.py")
            time.sleep(5)
            intento += 1
            continue
        
        print("✅ Servidor OK - ejecutando test...")
        
        # Ejecutar test
        success, stdout, stderr = ejecutar_test()
        
        if success:
            print("🎉 ¡TEST PASÓ!")
            print("\n📋 Output del test:")
            print("-" * 50)
            print(stdout)
            print("-" * 50)
            sys.exit(0)
        else:
            print("❌ Test falló")
            if stdout:
                print("STDOUT:", stdout[-500:])  # Últimos 500 chars
            if stderr:
                print("STDERR:", stderr[-500:])  # Últimos 500 chars
        
        intento += 1
        if intento <= max_intentos:
            print(f"⏳ Esperando 3 segundos antes del siguiente intento...")
            time.sleep(3)
    
    print(f"\n❌ FALLÓ DESPUÉS DE {max_intentos} INTENTOS")
    print("💡 Revisa los logs del servidor para debuggear más")
    sys.exit(1)
