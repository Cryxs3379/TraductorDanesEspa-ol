#!/usr/bin/env python3
"""
Script de verificación para probar el sistema anti-truncado.
"""
import requests
import json
import time

def test_anti_truncado():
    """Prueba el sistema anti-truncado con texto largo."""
    
    # Texto largo similar al que reportaste (2180+ caracteres)
    texto_largo = 'Este es un texto largo para probar que el sistema anti-truncado funciona correctamente. ' * 50
    
    print(f"🧪 Probando texto de {len(texto_largo)} caracteres...")
    
    # Test 1: Modo Auto (sin max_new_tokens)
    print("\n1️⃣ Test Modo Auto (sin max_new_tokens):")
    payload_auto = {
        'text': texto_largo,
        'direction': 'es-da'
    }
    
    try:
        response = requests.post('http://localhost:8000/translate', json=payload_auto, timeout=30)
        if response.status_code == 200:
            data = response.json()
            translation = data['translations'][0]
            print(f"   ✅ ÉXITO: {len(texto_largo)} chars → {len(translation)} chars")
            print(f"   📝 Primeros 100 chars: {translation[:100]}...")
            print(f"   📝 Últimos 100 chars: ...{translation[-100:]}")
            
            # Verificar que no está truncado
            if len(translation) > len(texto_largo) * 0.3:  # Al menos 30% de la longitud original
                print("   🎯 RESULTADO: No truncado - SISTEMA FUNCIONANDO")
            else:
                print("   ⚠️  RESULTADO: Posiblemente truncado")
        else:
            print(f"   ❌ Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"   ❌ Error de conexión: {e}")
    
    # Test 2: Modo Manual con elevación
    print("\n2️⃣ Test Modo Manual con elevación (strict_max=false):")
    payload_manual = {
        'text': texto_largo,
        'direction': 'es-da',
        'max_new_tokens': 64,  # muy bajo
        'strict_max': False    # permitir elevación
    }
    
    try:
        response = requests.post('http://localhost:8000/translate', json=payload_manual, timeout=30)
        if response.status_code == 200:
            data = response.json()
            translation = data['translations'][0]
            print(f"   ✅ ÉXITO: {len(texto_largo)} chars → {len(translation)} chars")
            print("   🎯 RESULTADO: Elevación automática funcionó")
        else:
            print(f"   ❌ Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"   ❌ Error de conexión: {e}")
    
    # Test 3: Modo Manual estricto (puede truncar)
    print("\n3️⃣ Test Modo Manual estricto (strict_max=true):")
    payload_strict = {
        'text': texto_largo,
        'direction': 'es-da',
        'max_new_tokens': 32,  # muy bajo
        'strict_max': True     # NO elevar
    }
    
    try:
        response = requests.post('http://localhost:8000/translate', json=payload_strict, timeout=30)
        if response.status_code == 200:
            data = response.json()
            translation = data['translations'][0]
            print(f"   ✅ ÉXITO: {len(texto_largo)} chars → {len(translation)} chars")
            print("   🎯 RESULTADO: Respetó límite estricto (puede truncar)")
        else:
            print(f"   ❌ Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"   ❌ Error de conexión: {e}")

def test_health():
    """Verifica que el servidor esté funcionando."""
    try:
        response = requests.get('http://localhost:8000/health', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"🏥 Health: {data.get('status', 'unknown')}")
            print(f"🤖 Modelo cargado: {data.get('model_loaded', False)}")
            return True
        else:
            print(f"❌ Health check falló: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ No se puede conectar al servidor: {e}")
        return False

if __name__ == "__main__":
    print("🔍 VERIFICACIÓN DEL SISTEMA ANTI-TRUNCADO")
    print("=" * 50)
    
    # Verificar que el servidor esté corriendo
    if test_health():
        print("\n" + "=" * 50)
        test_anti_truncado()
        print("\n" + "=" * 50)
        print("✅ Verificación completada")
    else:
        print("\n❌ El servidor no está corriendo. Ejecuta:")
        print("   python start_server.py")
