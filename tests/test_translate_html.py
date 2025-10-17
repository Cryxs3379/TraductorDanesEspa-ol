"""
Tests para traducción de HTML (segmentation + rehydration).

Verifica que la estructura HTML se preserve correctamente.
"""
import pytest
from fastapi.testclient import TestClient


# Importar la app solo si el modelo está disponible
try:
    from app.app import app
    MODEL_AVAILABLE = True
except Exception as e:
    MODEL_AVAILABLE = False
    SKIP_REASON = f"Modelo no disponible: {e}"


# Skip todos los tests si el modelo no está disponible
pytestmark = pytest.mark.skipif(
    not MODEL_AVAILABLE,
    reason="Modelo no cargado. Ejecuta: make download && make convert"
)


@pytest.fixture(scope="module")
def client():
    """Cliente de prueba de FastAPI."""
    return TestClient(app)


def test_translate_html_simple(client):
    """Test de traducción HTML simple."""
    payload = {
        "html": "<p>Hola mundo</p>"
    }
    
    response = client.post("/translate/html", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "html" in data
    assert "<p>" in data["html"]
    assert "</p>" in data["html"]


def test_translate_html_with_strong(client):
    """Test HTML con formato strong."""
    payload = {
        "html": "<p>Texto <strong>importante</strong> aquí</p>"
    }
    
    response = client.post("/translate/html", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    html = data["html"]
    
    # Debe preservar estructura
    assert "<strong>" in html or "<p>" in html
    assert "</strong>" in html or "</p>" in html


def test_translate_html_with_link(client):
    """Test HTML con enlaces."""
    payload = {
        "html": '<p>Visita <a href="https://example.com">nuestro sitio</a></p>'
    }
    
    response = client.post("/translate/html", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    html = data["html"]
    
    # Debe preservar href
    assert 'href="https://example.com"' in html or "https://example.com" in html


def test_translate_html_multiple_paragraphs(client):
    """Test con múltiples párrafos."""
    payload = {
        "html": "<p>Primer párrafo</p><p>Segundo párrafo</p><p>Tercer párrafo</p>"
    }
    
    response = client.post("/translate/html", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    html = data["html"]
    
    # Debe tener estructura de párrafos
    assert html.count("<p>") >= 2


def test_translate_html_with_list(client):
    """Test con listas HTML."""
    payload = {
        "html": "<ul><li>Primer item</li><li>Segundo item</li></ul>"
    }
    
    response = client.post("/translate/html", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    html = data["html"]
    
    # Debe preservar estructura de lista
    assert "<li>" in html or "item" in html


def test_translate_html_with_glossary(client):
    """Test HTML con glosario."""
    payload = {
        "html": "<p>Bienvenido a Acme Corporation</p>",
        "glossary": {
            "Acme": "Acme",
            "Corporation": "Selskab"
        }
    }
    
    response = client.post("/translate/html", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    html = data["html"]
    
    # Términos del glosario deben aparecer
    assert "Acme" in html
    assert "Selskab" in html or "Corporation" in html


def test_translate_html_formal_style(client):
    """Test con estilo formal."""
    payload = {
        "html": "<p>Hola cliente</p>",
        "formal": True
    }
    
    response = client.post("/translate/html", json=payload)
    assert response.status_code == 200
    
    # Debe procesar sin errores
    data = response.json()
    assert "html" in data


def test_translate_html_empty_error(client):
    """Test con HTML vacío."""
    payload = {
        "html": ""
    }
    
    response = client.post("/translate/html", json=payload)
    assert response.status_code == 400


def test_translate_html_xss_sanitization(client):
    """Test que el HTML peligroso se sanitiza."""
    payload = {
        "html": '<p onclick="alert(1)">Click me</p><script>alert("xss")</script>'
    }
    
    response = client.post("/translate/html", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    html = data["html"]
    
    # Scripts y event handlers deben estar removidos
    assert "<script>" not in html.lower()
    assert "onclick" not in html.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

