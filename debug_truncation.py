#!/usr/bin/env python3
"""
Script para debuggear el problema de truncado.
"""
import requests
import json
import sys

def debug_request(payload, description):
    """Realiza request y muestra información de debug."""
    print(f"\n🔍 {description}")
    print(f"📤 Payload enviado:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    
    try:
        response = requests.post('http://localhost:8000/translate', json=payload, timeout=30)
        
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            translation = data["translations"][0]
            
            print(f"📏 Longitud entrada: {len(payload['text'])} chars")
            print(f"📏 Longitud salida:  {len(translation)} chars")
            print(f"📝 Traducción: {translation[:100]}...")
            
            # Verificar si parece truncada
            ratio = len(translation) / len(payload['text'])
            if ratio < 0.3:
                print("❌ POSIBLE TRUNCADO: Ratio muy bajo")
            else:
                print(f"✅ Ratio normal: {ratio:.2%}")
                
            return translation
        else:
            print(f"❌ Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Excepción: {e}")
        return None

def main():
    print("🔍 DEBUGGING TRUNCATION ISSUE")
    print("=" * 50)
    
    # Test 1: Modo Auto (sin max_new_tokens)
    print("\n🧪 TEST 1: Modo Auto")
    texto_largo = "Este es un texto largo para probar que no se trunca sistemáticamente. " * 50
    
    payload1 = {
        "text": texto_largo,
        "direction": "es-da"
        # Sin max_new_tokens = modo Auto
    }
    
    result1 = debug_request(payload1, "Sin max_new_tokens (Auto)")
    
    # Test 2: Con max_new_tokens explícito None
    print("\n🧪 TEST 2: max_new_tokens=None explícito")
    payload2 = {
        "text": texto_largo,
        "direction": "es-da",
        "max_new_tokens": None
    }
    
    result2 = debug_request(payload2, "con max_new_tokens=None")
    
    # Test 3: Modo Manual con límite alto
    print("\n🧪 TEST 3: Modo Manual con límite alto")
    payload3 = {
        "text": texto_largo,
        "direction": "es-da",
        "max_new_tokens": 512,
        "strict_max": False
    }
    
    result3 = debug_request(payload3, "Manual con límite alto")
    
    # Test 4: Modo Manual estricto con límite bajo
    print("\n🧪 TEST 4: Modo Manual estricto")
    payload4 = {
        "text": texto_largo,
        "direction": "es-da",
        "max_new_tokens": 64,
        "strict_max": True
    }
    
    result4 = debug_request(payload4, "Manual estricto (debería truncar)")
    
    # Comparación final
    print("\n" + "=" * 50)
    print("📊 RESUMEN")
    
    if result1:
        print(f"Auto:     {len(result1)} chars")
    if result2:
        print(f"None:     {len(result2)} chars")
    if result3:
        print(f"Manual:   {len(result3)} chars")
    if result4:
        print(f"Strict:   {len(result4)} chars (debería ser más corto)")
    
    # Verificar si hay diferencia problemática
    if result1 and result2 and len(result1) != len(result2):
        print("⚠️  DIFERENCIA DETECTADA entre Auto y None")
    
    if result1 and result3 and len(result1) < len(result3):
        print("⚠️  Problema: Auto produce traducción más corta que Manual")

if __name__ == "__main__":
    main()
