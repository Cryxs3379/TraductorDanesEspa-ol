"""
Tests para verificar que el fix de truncado funciona correctamente.
"""
import pytest
from fastapi.testclient import TestClient
from app.app import app


client = TestClient(app)


def test_auto_mode_no_max_tokens():
    """Test que en modo Auto no se envía max_new_tokens y no hay truncado."""
    # Texto largo que debería activar el cálculo adaptativo
    long_text = "Este es un texto largo para probar que no se trunca. " * 100  # ~4000 chars
    
    payload = {
        "text": long_text,
        "direction": "es-da"
        # No enviar max_new_tokens - debería usar cálculo adaptativo
    }
    
    response = client.post("/translate", json=payload)
    
    if response.status_code == 503:
        pytest.skip("Modelo no cargado - ejecutar con servidor real")
    
    assert response.status_code == 200
    
    data = response.json()
    translation = data["translations"][0]
    
    # Verificar que no está truncado
    assert len(translation) > 500, f"Traducción parece truncada: {len(translation)} chars"
    
    # Verificar que contiene contenido sustancial del final
    assert len(translation) > len(long_text) * 0.2, "Traducción demasiado corta"


def test_manual_mode_respects_limit():
    """Test que en modo Manual se respeta el límite especificado."""
    text = "Este es un texto que debe ser truncado intencionalmente. " * 50
    
    payload = {
        "text": text,
        "direction": "es-da",
        "max_new_tokens": 64,  # muy bajo para causar truncado
        "strict_max": True     # respetar el límite
    }
    
    response = client.post("/translate", json=payload)
    
    if response.status_code == 503:
        pytest.skip("Modelo no cargado - ejecutar con servidor real")
    
    assert response.status_code == 200
    
    data = response.json()
    translation = data["translations"][0]
    
    # Con límite muy bajo y strict_max=True, debería truncar
    assert len(translation) < len(text) * 0.8, "No se respetó el límite estricto"
    
    print(f"Texto: {len(text)} chars, Traducción: {len(translation)} chars (truncado como esperado)")


def test_manual_mode_with_elevation():
    """Test que en modo Manual sin strict_max se eleva el límite si es muy bajo."""
    text = "Este es un texto largo que necesita más tokens para traducirse completamente. " * 80
    
    payload = {
        "text": text,
        "direction": "es-da",
        "max_new_tokens": 64,  # muy bajo
        "strict_max": False    # permitir elevación
    }
    
    response = client.post("/translate", json=payload)
    
    if response.status_code == 503:
        pytest.skip("Modelo no cargado - ejecutar con servidor real")
    
    assert response.status_code == 200
    
    data = response.json()
    translation = data["translations"][0]
    
    # Debería haber sido elevado y no truncado severamente
    assert len(translation) > 200, "No se aplicó elevación automática"


def test_long_html_no_truncation():
    """Test que HTML largo no se trunca en modo Auto."""
    long_html = f"""
    <html>
    <body>
        <p>Este es el primer párrafo de un correo muy largo.</p>
        <p>Aquí hay más contenido que necesita ser traducido completamente.</p>
        <p>Este es el párrafo final que confirma que no hay truncado.</p>
    </body>
    </html>
    """
    
    payload = {
        "html": long_html,
        "direction": "es-da"
        # No enviar max_new_tokens - modo Auto
    }
    
    response = client.post("/translate/html", json=payload)
    
    if response.status_code == 503:
        pytest.skip("Modelo no cargado - ejecutar con servidor real")
    
    assert response.status_code == 200
    
    data = response.json()
    translated_html = data["html"]
    
    # Verificar que contiene todos los párrafos
    assert "párrafo final" in translated_html.lower() or "sidste afsnit" in translated_html.lower(), \
        "HTML parece truncado - falta el párrafo final"
    
    # Verificar estructura HTML básica
    assert "<p>" in translated_html and "</p>" in translated_html, "Estructura HTML perdida"


def test_medium_text_no_segmentation():
    """Test que texto mediano no se segmenta innecesariamente."""
    # Texto mediano que no debería activar segmentación
    medium_text = "Este es un texto de longitud media. " * 30  # ~900 chars
    
    payload = {
        "text": medium_text,
        "direction": "es-da"
    }
    
    response = client.post("/translate", json=payload)
    
    if response.status_code == 503:
        pytest.skip("Modelo no cargado - ejecutar con servidor real")
    
    assert response.status_code == 200
    
    data = response.json()
    translation = data["translations"][0]
    
    # Verificar que la traducción es completa y no se perdió contenido del inicio
    assert len(translation) > 100, "Traducción demasiado corta"
    
    # El número de segmentos debería ser 1 (no segmentado)
    # Esto se puede verificar si el endpoint devuelve segments_count
    if "segments_count" in data:
        assert data["segments_count"] == 1, "Texto mediano fue segmentado innecesariamente"


def test_backwards_compatibility():
    """Test que el API sigue siendo compatible con requests que envían max_new_tokens."""
    text = "Hola mundo, esto es una prueba de compatibilidad."
    
    # Test con max_new_tokens explícito (comportamiento legacy)
    payload = {
        "text": text,
        "direction": "es-da",
        "max_new_tokens": 256  # valor explícito
    }
    
    response = client.post("/translate", json=payload)
    
    if response.status_code == 503:
        pytest.skip("Modelo no cargado - ejecutar con servidor real")
    
    assert response.status_code == 200
    
    data = response.json()
    assert len(data["translations"]) > 0
    assert data["translations"][0].strip() != "", "Traducción vacía"


if __name__ == "__main__":
    # Ejecutar tests básicos si se llama directamente
    print("🧪 Ejecutando tests básicos de truncado...")
    
    try:
        test_auto_mode_no_max_tokens()
        print("✅ test_auto_mode_no_max_tokens: PASS")
    except Exception as e:
        print(f"❌ test_auto_mode_no_max_tokens: FAIL - {e}")
    
    try:
        test_medium_text_no_segmentation()
        print("✅ test_medium_text_no_segmentation: PASS")
    except Exception as e:
        print(f"❌ test_medium_text_no_segmentation: FAIL - {e}")
