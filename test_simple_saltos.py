#!/usr/bin/env python3
"""
Test simple para verificar que los saltos de línea se preservan.
"""
import requests
import json

def test_simple():
    """Test simple con saltos de línea."""
    print("🧪 TEST SIMPLE - SALTOS DE LÍNEA")
    print("=" * 50)
    
    # Texto simple con saltos de línea
    text = """Primera línea.
Segunda línea.

Tercera línea después de salto doble."""
    
    print("📝 TEXTO ORIGINAL:")
    print("-" * 30)
    print(repr(text))  # Mostrar con \n visibles
    print("-" * 30)
    
    payload = {
        "text": text,
        "direction": "es-da"
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/translate",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            translation = data["translations"][0]
            
            print("\n📊 RESULTADO:")
            print("-" * 30)
            print(repr(translation))  # Mostrar con \n visibles
            print("-" * 30)
            
            # Verificar saltos de línea
            original_breaks = text.count('\n')
            translated_breaks = translation.count('\n')
            
            print(f"\n🔍 ANÁLISIS:")
            print(f"   Saltos originales: {original_breaks}")
            print(f"   Saltos traducidos: {translated_breaks}")
            
            if translated_breaks >= original_breaks:
                print("✅ CORRECTO: Saltos de línea preservados")
                return True
            else:
                print("❌ PROBLEMA: Se perdieron saltos de línea")
                return False
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_simple()
