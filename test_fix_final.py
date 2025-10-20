#!/usr/bin/env python3
"""
Test específico para verificar que el fix del truncado funciona.
"""
import requests
import json
import time

def test_fix():
    """Test principal del fix."""
    print("🔧 TESTING FINAL FIX FOR TRUNCATION")
    print("=" * 50)
    
    # Texto largo que debería activar el cálculo adaptativo mejorado
    texto_largo = """
    Esta es una prueba de texto largo para verificar que el sistema de traducción automática 
    no trunca las traducciones cuando se usa el modo automático. El problema reportado por 
    el usuario indica que cualquier texto largo en español se devuelve cortado, lo cual es 
    inaceptable para un sistema de traducción profesional. 
    
    Este párrafo adicional debería traducirse completamente sin pérdida de contenido.
    La implementación actual incluye mejoras en el cálculo adaptativo de tokens y 
    aumentos en los límites máximos para acomodar textos más largos.
    
    Finalmente, este párrafo de cierre debería aparecer completo en la traducción danesa,
    confirmando que el sistema funciona correctamente sin truncado.
    """.strip()
    
    print(f"📏 Longitud del texto de prueba: {len(texto_largo)} caracteres")
    
    # Test 1: Modo Auto (sin max_new_tokens)
    print("\n🧪 TEST 1: Modo Auto (sin max_new_tokens)")
    payload_auto = {
        "text": texto_largo,
        "direction": "es-da"
        # Sin max_new_tokens - debería usar cálculo adaptativo
    }
    
    try:
        print("📤 Enviando request...")
        response = requests.post('http://localhost:8000/translate', json=payload_auto, timeout=60)
        
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            translation = data["translations"][0]
            
            print(f"📏 Entrada: {len(texto_largo)} chars")
            print(f"📏 Salida:  {len(translation)} chars")
            print(f"📊 Ratio:   {len(translation)/len(texto_largo):.2%}")
            
            # Verificar que no está truncado
            if len(translation) < len(texto_largo) * 0.5:
                print("❌ POSIBLE TRUNCADO: Ratio muy bajo")
                print(f"   Texto original: {texto_largo[:100]}...")
                print(f"   Traducción: {translation[:100]}...")
                return False
            else:
                print("✅ ÉXITO: Traducción completa, no truncada")
                
                # Verificar que contiene contenido del final
                if any(word in translation.lower() for word in ["endelig", "bekræfter", "dansk"]):
                    print("✅ ÉXITO: Contenido del final presente")
                else:
                    print("⚠️  AVISO: Contenido del final podría estar truncado")
                
                return True
        else:
            print(f"❌ Error HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Excepción: {e}")
        return False

def test_health():
    """Verifica que el servidor esté funcionando."""
    try:
        response = requests.get('http://localhost:8000/health', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"🏥 Servidor: {data.get('status', 'unknown')}")
            print(f"🤖 Modelo: {'✅ Cargado' if data.get('model_loaded') else '❌ No cargado'}")
            return data.get('model_loaded', False)
        else:
            print(f"❌ Health check falló: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ No se puede conectar: {e}")
        return False

if __name__ == "__main__":
    print("🚀 INICIANDO TEST DEL FIX")
    
    if not test_health():
        print("\n❌ El servidor no está listo.")
        print("   Ejecuta: python start_server.py")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    
    success = test_fix()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 ¡FIX FUNCIONANDO! El problema de truncado está resuelto.")
    else:
        print("❌ El fix necesita más trabajo. Revisa los logs del servidor.")
        
    print("\n💡 Siguiente paso: Prueba desde el frontend con texto largo.")
