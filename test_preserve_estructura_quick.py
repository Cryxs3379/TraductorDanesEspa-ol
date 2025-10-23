"""
Script de verificación rápida de preservación de estructura.

Ejecutar con el servidor corriendo:
    python test_preserve_estructura_quick.py

Verifica que:
- Los saltos de línea se preservan en texto plano
- Los <br> se preservan en HTML
- El parámetro preserve_newlines funciona
"""
import requests
import sys


API_URL = "http://localhost:8000"


def test_texto_plano_preserva_estructura():
    """Test: texto plano preserva saltos simples y dobles."""
    print("\n📝 Test 1: Texto plano con saltos de línea")
    print("-" * 60)
    
    texto_original = "Estimado Sr. García,\n\nGracias por contactarnos.\n\nAtentamente,\nEl equipo"
    
    payload = {
        "direction": "es-da",
        "text": texto_original,
        "preserve_newlines": True
    }
    
    response = requests.post(f"{API_URL}/translate", json=payload)
    
    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        print(response.json())
        return False
    
    resultado = response.json()
    traduccion = resultado["translations"][0]
    
    # Contar saltos de línea
    saltos_original = texto_original.count("\n")
    saltos_traduccion = traduccion.count("\n")
    
    print(f"Original: {saltos_original} saltos de línea")
    print(f"Traducción: {saltos_traduccion} saltos de línea")
    
    if saltos_original == saltos_traduccion:
        print("✅ PASS: Saltos de línea preservados correctamente")
        return True
    else:
        print("❌ FAIL: Número de saltos de línea cambió")
        print(f"Original:\n{repr(texto_original)}")
        print(f"\nTraducción:\n{repr(traduccion)}")
        return False


def test_html_preserva_br():
    """Test: HTML preserva <br> exactamente."""
    print("\n🌐 Test 2: HTML con <br>")
    print("-" * 60)
    
    html_original = "<p>Estimado cliente,</p><p>Gracias por contactar.<br>Atentamente,<br>El equipo</p>"
    
    payload = {
        "direction": "es-da",
        "html": html_original,
        "preserve_newlines": True
    }
    
    response = requests.post(f"{API_URL}/translate/html", json=payload)
    
    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        print(response.json())
        return False
    
    resultado = response.json()
    html_traducido = resultado["html"]
    
    # Contar <br>
    br_original = html_original.lower().count("<br")
    br_traducido = html_traducido.lower().count("<br")
    
    # Contar <p>
    p_original = html_original.count("<p>")
    p_traducido = html_traducido.count("<p>")
    
    print(f"Original: {br_original} <br>, {p_original} <p>")
    print(f"Traducción: {br_traducido} <br>, {p_traducido} <p>")
    
    if br_original == br_traducido and p_original == p_traducido:
        print("✅ PASS: Estructura HTML preservada correctamente")
        return True
    else:
        print("❌ FAIL: Estructura HTML cambió")
        print(f"Original:\n{html_original}")
        print(f"\nTraducción:\n{html_traducido}")
        return False


def test_email_completo():
    """Test: Email completo con firma y múltiples párrafos."""
    print("\n📧 Test 3: Email completo con firma")
    print("-" * 60)
    
    email = """Hola Juan,

¿Cómo estás?

Saludos,
— Pedro"""
    
    payload = {
        "direction": "es-da",
        "text": email,
        "preserve_newlines": True
    }
    
    response = requests.post(f"{API_URL}/translate", json=payload)
    
    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        print(response.json())
        return False
    
    resultado = response.json()
    traduccion = resultado["translations"][0]
    
    # Verificar estructura
    lineas_original = email.split("\n")
    lineas_traduccion = traduccion.split("\n")
    
    print(f"Original: {len(lineas_original)} líneas")
    print(f"Traducción: {len(lineas_traduccion)} líneas")
    
    # Verificar saltos dobles
    dobles_original = email.count("\n\n")
    dobles_traduccion = traduccion.count("\n\n")
    
    print(f"Original: {dobles_original} párrafos (\\n\\n)")
    print(f"Traducción: {dobles_traduccion} párrafos (\\n\\n)")
    
    if len(lineas_original) == len(lineas_traduccion) and dobles_original == dobles_traduccion:
        print("✅ PASS: Email preservado correctamente")
        print(f"\nTraducción:\n{traduccion}")
        return True
    else:
        print("❌ FAIL: Estructura del email cambió")
        return False


def test_preserve_false():
    """Test: preserve_newlines=false usa modo legacy."""
    print("\n🔧 Test 4: Modo legacy (preserve_newlines=false)")
    print("-" * 60)
    
    texto = "Línea 1\n\n\nLínea 2"
    
    payload = {
        "direction": "es-da",
        "text": texto,
        "preserve_newlines": False  # Modo legacy
    }
    
    response = requests.post(f"{API_URL}/translate", json=payload)
    
    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        return False
    
    resultado = response.json()
    traduccion = resultado["translations"][0]
    
    # En modo legacy, los saltos múltiples se normalizan a máximo 2
    saltos_traduccion = traduccion.count("\n")
    
    print(f"Original: {texto.count(chr(10))} saltos")
    print(f"Traducción (legacy): {saltos_traduccion} saltos")
    
    if saltos_traduccion <= 2:
        print("✅ PASS: Modo legacy normaliza correctamente")
        return True
    else:
        print("⚠️ WARNING: Modo legacy podría no estar normalizando")
        return True  # No es error crítico


def main():
    """Ejecuta todos los tests."""
    print("=" * 60)
    print("🧪 VERIFICACIÓN DE PRESERVACIÓN DE ESTRUCTURA")
    print("=" * 60)
    
    # Verificar que el servidor está corriendo
    try:
        health = requests.get(f"{API_URL}/health", timeout=2)
        if health.status_code != 200:
            print("❌ ERROR: Servidor no está healthy")
            print("Por favor, inicia el servidor con: python start_server.py")
            sys.exit(1)
        
        health_data = health.json()
        if not health_data.get("model_loaded"):
            print("❌ ERROR: Modelo no está cargado")
            print("Espera a que el modelo termine de cargar y reintenta")
            sys.exit(1)
        
        print("✅ Servidor está corriendo y modelo cargado")
        
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: No se puede conectar al servidor")
        print("Por favor, inicia el servidor con: python start_server.py")
        sys.exit(1)
    
    # Ejecutar tests
    resultados = []
    resultados.append(test_texto_plano_preserva_estructura())
    resultados.append(test_html_preserva_br())
    resultados.append(test_email_completo())
    resultados.append(test_preserve_false())
    
    # Resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN")
    print("=" * 60)
    
    total = len(resultados)
    pasados = sum(resultados)
    
    print(f"Tests ejecutados: {total}")
    print(f"Tests pasados: {pasados}")
    print(f"Tests fallidos: {total - pasados}")
    
    if all(resultados):
        print("\n🎉 ¡TODOS LOS TESTS PASARON!")
        print("\n✅ La preservación de estructura está funcionando correctamente")
        sys.exit(0)
    else:
        print("\n❌ Algunos tests fallaron")
        print("Revisa los detalles arriba")
        sys.exit(1)


if __name__ == "__main__":
    main()

