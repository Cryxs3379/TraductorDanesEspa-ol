#!/usr/bin/env python3
"""
Script para probar que el problema de truncado se ha solucionado.
"""
import requests
import json

def test_texto_corto():
    """Prueba con texto corto que no debería segmentarse."""
    
    # Texto similar al de la imagen del usuario
    texto_corto = "lengua, tú no, porque me la corté ayer. Estuve jugando con el diccionario Elefen por un rato, buscando cualquier palabra aleatoria que se me ocurriera."
    
    print(f"🧪 Probando texto corto de {len(texto_corto)} caracteres...")
    print(f"📝 Texto original: {texto_corto}")
    
    payload = {
        'text': texto_corto,
        'direction': 'es-da'
    }
    
    try:
        response = requests.post('http://localhost:8000/translate', json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            translation = data['translations'][0]
            print(f"✅ Traducción: {translation}")
            print(f"📊 Longitud: {len(texto_corto)} → {len(translation)} caracteres")
            
            # Verificar que no se perdió el inicio
            if "lengua" in texto_corto.lower() and "tunge" in translation.lower():
                print("🎯 ÉXITO: El inicio del texto se tradujo correctamente")
            else:
                print("❌ PROBLEMA: Se perdió el inicio del texto")
                print(f"   Original empieza con: '{texto_corto[:50]}...'")
                print(f"   Traducción empieza con: '{translation[:50]}...'")
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Error de conexión: {e}")

def test_texto_largo():
    """Prueba con texto largo que SÍ debería segmentarse."""
    
    texto_largo = "Este es un texto largo para probar la segmentación. " * 100  # ~5000 chars
    
    print(f"\n🧪 Probando texto largo de {len(texto_largo)} caracteres...")
    
    payload = {
        'text': texto_largo,
        'direction': 'es-da'
    }
    
    try:
        response = requests.post('http://localhost:8000/translate', json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            translation = data['translations'][0]
            print(f"✅ Traducción completada: {len(texto_largo)} → {len(translation)} caracteres")
            
            # Verificar que está completo
            if len(translation) > len(texto_largo) * 0.3:
                print("🎯 ÉXITO: Texto largo traducido completamente")
            else:
                print("❌ PROBLEMA: Texto largo truncado")
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Error de conexión: {e}")

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
    print("🔍 VERIFICACIÓN DEL FIX DE TRUNCADO")
    print("=" * 50)
    
    # Verificar que el servidor esté corriendo
    if test_health():
        print("\n" + "=" * 50)
        test_texto_corto()
        test_texto_largo()
        print("\n" + "=" * 50)
        print("✅ Verificación completada")
    else:
        print("\n❌ El servidor no está corriendo. Ejecuta:")
        print("   python start_server.py")



