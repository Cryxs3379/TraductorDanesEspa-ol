#!/usr/bin/env python3
"""
Test para verificar el problema con saltos de línea en la traducción.
"""
import requests
import json

def test_line_breaks():
    """Test con texto que tiene saltos de línea."""
    print("🧪 TESTING SALTOS DE LÍNEA EN TRADUCCIÓN")
    print("=" * 60)
    
    # Texto con saltos de línea y estructura
    text_with_breaks = """Sencillas, sonrientes y llenas de ingenuidad, como la musulmana Schehrazada, su madre suculenta que las dió a luz en el misterio; fermentando con emoción en los brazos de un príncipe sublime —lúbrico y feroz—, bajo la mirada enternecida de Alah, clemente y misericordioso.

 Al venir al mundo fueron delicadamente mecidas por las manos de la lustral Doniazada, 
su buena tía, que grabó sus nombres sobre hojas de oro coloreadas de húmedas pedrerías y las cuidó bajo el terciopelo de sus pupilas hasta la adolescencia dura, para esparcirlas después, voluptuosas y libres, sobre el mundo oriental, eternizado por su sonrisa."""
    
    print("📝 TEXTO ORIGINAL:")
    print("-" * 40)
    print(text_with_breaks)
    print("-" * 40)
    print(f"Longitud: {len(text_with_breaks)} caracteres")
    print(f"Saltos de línea: {text_with_breaks.count(chr(10))}")
    
    payload = {
        "text": text_with_breaks,
        "direction": "es-da",
        "formal": False
    }
    
    try:
        print("\n🔄 Enviando request...")
        response = requests.post(
            "http://localhost:8000/translate",
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            translation = data["translations"][0]
            
            print("\n📊 RESULTADO:")
            print("-" * 40)
            print(translation)
            print("-" * 40)
            print(f"Longitud traducida: {len(translation)} caracteres")
            print(f"Saltos de línea traducidos: {translation.count(chr(10))}")
            
            # Análisis del problema
            original_breaks = text_with_breaks.count(chr(10))
            translated_breaks = translation.count(chr(10))
            
            print(f"\n🔍 ANÁLISIS:")
            print(f"   Saltos originales: {original_breaks}")
            print(f"   Saltos traducidos: {translated_breaks}")
            
            if translated_breaks < original_breaks:
                print("❌ PROBLEMA: Se perdieron saltos de línea")
                print("   La estructura se está rompiendo")
                return False
            elif translated_breaks == original_breaks:
                print("✅ CORRECTO: Saltos de línea preservados")
                return True
            else:
                print("⚠️  ADVERTENCIA: Más saltos de línea que el original")
                return True
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return False

def test_html_structure():
    """Test con estructura HTML para correos."""
    print("\n" + "=" * 60)
    print("🧪 TESTING ESTRUCTURA HTML")
    print("=" * 60)
    
    html_text = """<p>Sencillas, sonrientes y llenas de ingenuidad, como la musulmana Schehrazada, su madre suculenta que las dió a luz en el misterio; fermentando con emoción en los brazos de un príncipe sublime —lúbrico y feroz—, bajo la mirada enternecida de Alah, clemente y misericordioso.</p>

<p>Al venir al mundo fueron delicadamente mecidas por las manos de la lustral Doniazada, 
su buena tía, que grabó sus nombres sobre hojas de oro coloreadas de húmedas pedrerías y las cuidó bajo el terciopelo de sus pupilas hasta la adolescencia dura, para esparcirlas después, voluptuosas y libres, sobre el mundo oriental, eternizado por su sonrisa.</p>"""
    
    print("📝 HTML ORIGINAL:")
    print("-" * 40)
    print(html_text)
    print("-" * 40)
    
    payload = {
        "html": html_text,
        "direction": "es-da",
        "formal": False
    }
    
    try:
        print("\n🔄 Enviando request HTML...")
        response = requests.post(
            "http://localhost:8000/translate/html",
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            translation = data["html"]
            
            print("\n📊 RESULTADO HTML:")
            print("-" * 40)
            print(translation)
            print("-" * 40)
            
            # Verificar que se mantenga la estructura HTML
            if "<p>" in translation and "</p>" in translation:
                print("✅ CORRECTO: Estructura HTML preservada")
                return True
            else:
                print("❌ PROBLEMA: Estructura HTML perdida")
                return False
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return False

def main():
    """Ejecutar tests de saltos de línea y estructura."""
    print("🎯 TESTING PROBLEMA DE SALTOS DE LÍNEA Y ESTRUCTURA")
    print("=" * 60)
    
    # Test 1: Saltos de línea en texto plano
    result1 = test_line_breaks()
    
    # Test 2: Estructura HTML
    result2 = test_html_structure()
    
    # Resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE RESULTADOS")
    print("=" * 60)
    
    if result1 and result2:
        print("✅ TODOS LOS TESTS PASARON")
        print("   Los saltos de línea y estructura se preservan correctamente")
    elif result1 or result2:
        print("⚠️  MEJORA PARCIAL")
        print("   Algunos aspectos funcionan, otros necesitan ajustes")
    else:
        print("❌ PROBLEMA CONFIRMADO")
        print("   Los saltos de línea y estructura se están perdiendo")
        print("\n💡 SOLUCIONES NECESARIAS:")
        print("   1. Preservar saltos de línea en pre-procesamiento")
        print("   2. Mantener estructura en post-procesamiento")
        print("   3. Usar endpoint /translate/html para correos estructurados")

if __name__ == "__main__":
    main()
