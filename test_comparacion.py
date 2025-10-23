#!/usr/bin/env python3
"""
Test para comparar traducción con y sin saltos de línea.
"""
import requests
import json

def test_without_breaks():
    """Test sin saltos de línea (funciona bien)."""
    print("🧪 TEST SIN SALTOS DE LÍNEA")
    print("=" * 50)
    
    text_no_breaks = "Sencillas, sonrientes y llenas de ingenuidad, como la musulmana Schehrazada, su madre suculenta que las dió a luz en el misterio; fermentando con emoción en los brazos de un príncipe sublime —lúbrico y feroz—, bajo la mirada enternecida de Alah, clemente y misericordioso. Al venir al mundo fueron delicadamente mecidas por las manos de la lustral Doniazada, su buena tía, que grabó sus nombres sobre hojas de oro coloreadas de húmedas pedrerías y las cuidó bajo el terciopelo de sus pupilas hasta la adolescencia dura, para esparcirlas después, voluptuosas y libres, sobre el mundo oriental, eternizado por su sonrisa."
    
    payload = {
        "text": text_no_breaks,
        "direction": "es-da",
        "formal": False
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
            
            print(f"✅ SIN SALTOS: {len(translation)} caracteres")
            print(f"   Traducción: {translation[:100]}...")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        return False

def test_with_breaks():
    """Test con saltos de línea (problema)."""
    print("\n🧪 TEST CON SALTOS DE LÍNEA")
    print("=" * 50)
    
    text_with_breaks = """Sencillas, sonrientes y llenas de ingenuidad, como la musulmana Schehrazada, su madre suculenta que las dió a luz en el misterio; fermentando con emoción en los brazos de un príncipe sublime —lúbrico y feroz—, bajo la mirada enternecida de Alah, clemente y misericordioso.

 Al venir al mundo fueron delicadamente mecidas por las manos de la lustral Doniazada, 
su buena tía, que grabó sus nombres sobre hojas de oro coloreadas de húmedas pedrerías y las cuidó bajo el terciopelo de sus pupilas hasta la adolescencia dura, para esparcirlas después, voluptuosas y libres, sobre el mundo oriental, eternizado por su sonrisa."""
    
    print(f"📝 Saltos de línea en original: {text_with_breaks.count(chr(10))}")
    
    payload = {
        "text": text_with_breaks,
        "direction": "es-da",
        "formal": False
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
            
            print(f"📊 CON SALTOS: {len(translation)} caracteres")
            print(f"   Saltos en traducción: {translation.count(chr(10))}")
            print(f"   Traducción: {translation[:100]}...")
            
            # Verificar si se perdieron saltos
            original_breaks = text_with_breaks.count(chr(10))
            translated_breaks = translation.count(chr(10))
            
            if translated_breaks < original_breaks:
                print("❌ PROBLEMA: Se perdieron saltos de línea")
                return False
            else:
                print("✅ CORRECTO: Saltos de línea preservados")
                return True
        else:
            print(f"❌ Error: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Comparar ambos casos."""
    print("🎯 COMPARACIÓN: CON vs SIN SALTOS DE LÍNEA")
    print("=" * 60)
    
    # Test 1: Sin saltos (debería funcionar)
    result1 = test_without_breaks()
    
    # Test 2: Con saltos (problema actual)
    result2 = test_with_breaks()
    
    # Análisis
    print("\n" + "=" * 60)
    print("📊 ANÁLISIS DE RESULTADOS")
    print("=" * 60)
    
    if result1 and result2:
        print("✅ AMBOS TESTS PASARON")
        print("   El problema de saltos de línea está solucionado")
    elif result1 and not result2:
        print("❌ PROBLEMA CONFIRMADO")
        print("   Sin saltos: ✅ Funciona")
        print("   Con saltos: ❌ Se rompe")
        print("\n💡 SOLUCIÓN:")
        print("   1. Reiniciar servidor: python start_server.py")
        print("   2. La corrección en _normalize_text() debería solucionarlo")
    else:
        print("⚠️  RESULTADOS MIXTOS")
        print("   Revisar configuración del servidor")

if __name__ == "__main__":
    main()
