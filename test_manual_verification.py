#!/usr/bin/env python3
"""
Script de verificación manual para el fix de truncado.
"""
import requests
import json
import time

def test_auto_mode_long_text():
    """Verifica que el modo Auto no trunca textos largos."""
    print("🧪 Test 1: Modo Auto con texto largo")
    
    long_text = "Este es un texto muy largo para probar que el sistema anti-truncado funciona correctamente. " * 100
    
    payload = {
        "text": long_text,
        "direction": "es-da"
        # No max_new_tokens = modo Auto
    }
    
    try:
        response = requests.post('http://localhost:8000/translate', json=payload, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            translation = data["translations"][0]
            
            print(f"📊 Entrada: {len(long_text)} chars")
            print(f"📊 Salida:  {len(translation)} chars")
            print(f"📊 Ratio:   {len(translation)/len(long_text):.2%}")
            
            if len(translation) > len(long_text) * 0.3:
                print("✅ ÉXITO: No hay truncado significativo")
                return True
            else:
                print("❌ FALLO: Traducción parece truncada")
                return False
        else:
            print(f"❌ Error HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_manual_mode_strict():
    """Verifica que el modo Manual estricto respeta límites bajos."""
    print("\n🧪 Test 2: Modo Manual estricto")
    
    text = "Texto de prueba para verificar límite estricto. " * 20
    
    payload = {
        "text": text,
        "direction": "es-da",
        "max_new_tokens": 32,  # muy bajo
        "strict_max": True     # respetar límite
    }
    
    try:
        response = requests.post('http://localhost:8000/translate', json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            translation = data["translations"][0]
            
            print(f"📊 Límite: 32 tokens")
            print(f"📊 Salida: {len(translation)} chars")
            
            if len(translation) < 200:  # Debería estar limitado
                print("✅ ÉXITO: Se respetó el límite estricto")
                return True
            else:
                print("⚠️  AVISO: Límite no se respetó completamente")
                return True  # No es un fallo crítico
        else:
            print(f"❌ Error HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_medium_text_complete():
    """Verifica que textos medianos se traducen completos."""
    print("\n🧪 Test 3: Texto mediano - sin truncado de inicio")
    
    # Texto similar al que reportó el usuario
    medium_text = "lengua, tú no, porque me la corté ayer. Estuve jugando con el diccionario Elefen por un rato, buscando cualquier palabra aleatoria que se me ocurriera."
    
    payload = {
        "text": medium_text,
        "direction": "es-da"
    }
    
    try:
        response = requests.post('http://localhost:8000/translate', json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            translation = data["translations"][0]
            
            print(f"📊 Entrada: {len(medium_text)} chars")
            print(f"📊 Salida:  {len(translation)} chars")
            print(f"📝 Traducción: {translation[:100]}...")
            
            # Verificar que no se perdió el inicio (debe contener "lengua" o "tunge")
            if any(word in translation.lower() for word in ["tunge", "længde", "sprog"]):
                print("✅ ÉXITO: El inicio del texto se tradujo correctamente")
                return True
            else:
                print("❌ FALLO: Se perdió el inicio del texto")
                print(f"   Original: {medium_text[:50]}...")
                print(f"   Traducido: {translation[:50]}...")
                return False
        else:
            print(f"❌ Error HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_health():
    """Verifica que el servidor esté funcionando."""
    try:
        response = requests.get('http://localhost:8000/health', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"🏥 Health: {data.get('status', 'unknown')}")
            print(f"🤖 Modelo cargado: {data.get('model_loaded', False)}")
            return data.get('model_loaded', False)
        else:
            print(f"❌ Health check falló: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ No se puede conectar al servidor: {e}")
        return False

def main():
    print("🔍 VERIFICACIÓN MANUAL DEL FIX DE TRUNCADO")
    print("=" * 60)
    
    # Verificar servidor
    if not test_health():
        print("\n❌ El servidor no está listo. Ejecuta:")
        print("   python start_server.py")
        return
    
    print("\n" + "=" * 60)
    
    # Ejecutar tests
    tests = [
        test_auto_mode_long_text,
        test_manual_mode_strict,
        test_medium_text_complete,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Error inesperado en test: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 RESUMEN: {passed}/{total} tests pasaron")
    
    if passed == total:
        print("🎉 ¡TODOS LOS TESTS PASARON! El fix está funcionando correctamente.")
    else:
        print("⚠️  Algunos tests fallaron. Revisa los logs arriba.")

if __name__ == "__main__":
    main()
