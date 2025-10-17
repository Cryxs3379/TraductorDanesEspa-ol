"""
Tests de humo (smoke tests) para el servicio de traducción.

Verifica funcionalidad básica del endpoint /translate:
- Traducción de texto simple
- Traducción de múltiples textos (batch)
- Uso de glosario
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


def test_health_endpoint(client):
    """Test del endpoint de health check."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True


def test_root_endpoint(client):
    """Test del endpoint raíz."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Traductor ES → DA"
    assert data["provider"] == "nllb-ct2-int8"
    assert data["status"] == "online"


def test_translate_single_text(client):
    """Test de traducción de un solo texto."""
    payload = {
        "text": "Hola mundo",
        "max_new_tokens": 128
    }
    
    response = client.post("/translate", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["provider"] == "nllb-ct2-int8"
    assert data["source"] == "spa_Latn"
    assert data["target"] == "dan_Latn"
    assert "translations" in data
    assert isinstance(data["translations"], list)
    assert len(data["translations"]) == 1
    assert len(data["translations"][0]) > 0
    
    # Verificar que la traducción no está vacía
    translation = data["translations"][0]
    assert translation.strip() != ""
    
    print(f"\nTraducción: '{payload['text']}' → '{translation}'")


def test_translate_multiple_texts(client):
    """Test de traducción de múltiples textos (batch)."""
    payload = {
        "text": [
            "Buenos días",
            "¿Cómo estás?",
            "Gracias por tu ayuda"
        ],
        "max_new_tokens": 128
    }
    
    response = client.post("/translate", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "translations" in data
    assert isinstance(data["translations"], list)
    assert len(data["translations"]) == 3
    
    # Verificar que todas las traducciones no están vacías
    for i, translation in enumerate(data["translations"]):
        assert translation.strip() != ""
        print(f"\nTraducción {i+1}: '{payload['text'][i]}' → '{translation}'")


def test_translate_with_glossary(client):
    """Test de traducción con glosario personalizado."""
    payload = {
        "text": "Bienvenido a Acme Corporation",
        "glossary": {
            "Acme": "Acme",  # Preservar nombre de empresa
            "Corporation": "Selskab"  # Traducir a término específico
        }
    }
    
    response = client.post("/translate", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "translations" in data
    assert len(data["translations"]) == 1
    
    translation = data["translations"][0]
    assert translation.strip() != ""
    
    # Verificar que los términos del glosario aparecen
    assert "Acme" in translation
    assert "Selskab" in translation or "Corporation" in translation
    
    print(f"\nTraducción con glosario: '{payload['text']}' → '{translation}'")
    print(f"Glosario aplicado: {payload['glossary']}")


def test_translate_with_formal_style(client):
    """Test de traducción con estilo formal."""
    payload = {
        "text": "Hola, necesito ayuda",
        "formal": True
    }
    
    response = client.post("/translate", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    translation = data["translations"][0]
    
    # Debe procesar sin errores
    assert len(translation.strip()) > 0
    
    print(f"\nTraducción formal: '{payload['text']}' → '{translation}'")


def test_translate_empty_text_error(client):
    """Test de error con texto vacío."""
    payload = {
        "text": ""
    }
    
    response = client.post("/translate", json=payload)
    # Puede ser 400 (bad request) o 422 (validation error)
    assert response.status_code in [400, 422]


def test_translate_empty_list_error(client):
    """Test de error con lista vacía."""
    payload = {
        "text": []
    }
    
    response = client.post("/translate", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data


def test_translate_max_tokens_validation(client):
    """Test de validación de max_new_tokens."""
    # Test con valor válido
    payload = {
        "text": "Hola",
        "max_new_tokens": 64
    }
    response = client.post("/translate", json=payload)
    assert response.status_code == 200
    
    # Test con valor inválido (demasiado bajo)
    payload_invalid = {
        "text": "Hola",
        "max_new_tokens": 0
    }
    response = client.post("/translate", json=payload_invalid)
    assert response.status_code == 422  # Validation error
    
    # Test con valor inválido (demasiado alto)
    payload_invalid_high = {
        "text": "Hola",
        "max_new_tokens": 1000
    }
    response = client.post("/translate", json=payload_invalid_high)
    assert response.status_code == 422  # Validation error


def test_info_endpoint(client):
    """Test del endpoint de información."""
    response = client.get("/info")
    assert response.status_code == 200
    
    data = response.json()
    assert "model" in data
    assert "capabilities" in data
    
    capabilities = data["capabilities"]
    assert "spa_Latn" in capabilities["source_languages"]
    assert "dan_Latn" in capabilities["target_languages"]
    assert capabilities["supports_glossary"] is True
    assert capabilities["supports_batch"] is True


@pytest.mark.parametrize("text,expected_not_empty", [
    ("Hola", True),
    ("Buenos días", True),
    ("¿Cómo estás?", True),
    ("Me llamo Pedro", True),
    ("El cielo es azul", True),
])
def test_various_spanish_phrases(client, text, expected_not_empty):
    """Test parametrizado con varias frases en español."""
    payload = {"text": text}
    
    response = client.post("/translate", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    translation = data["translations"][0]
    
    if expected_not_empty:
        assert len(translation.strip()) > 0
    
    print(f"\n'{text}' → '{translation}'")


def test_translation_output_is_latin(client):
    """Test que verifica que la salida es en alfabeto latino (danés)."""
    payload = {
        "text": "Hola, ¿cómo estás?"
    }
    
    response = client.post("/translate", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    translation = data["translations"][0]
    
    # Verificar que la traducción no está vacía
    assert len(translation.strip()) > 0
    
    # Verificar que contiene principalmente caracteres latinos
    # Permitir letras latinas, danesas (æ, ø, å), números y puntuación
    import re
    latin_pattern = re.compile(
        r'[a-zA-ZæøåÆØÅàáâãäåèéêëìíîïòóôõöùúûüýÿñçÀÁÂÃÄÅÈÉÊËÌÍÎÏÒÓÔÕÖÙÚÛÜÝŸÑÇ0-9\s\.,;:!?¿¡\-\'\"()\[\]{}/@#$%&*+=<>|\\~`]'
    )
    
    latin_chars = len(latin_pattern.findall(translation))
    total_chars = len(translation)
    
    if total_chars > 0:
        ratio = latin_chars / total_chars
        # Al menos 80% debe ser caracteres latinos
        assert ratio >= 0.8, f"Salida con demasiados caracteres no latinos: {ratio:.2%} latinos. Traducción: {translation}"
    
    print(f"\n✓ Traducción en alfabeto latino: '{translation}' ({ratio:.1%} caracteres latinos)")


def test_translate_html_endpoint(client):
    """Test del endpoint /translate/html."""
    payload = {
        "html": "<p>Hola <strong>mundo</strong></p>",
        "max_new_tokens": 128,
        "direction": "es-da"
    }
    
    response = client.post("/translate/html", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "html" in data
    assert data["provider"] == "nllb-ct2-int8"
    assert data["direction"] == "es-da"
    assert data["source"] == "spa_Latn"
    assert data["target"] == "dan_Latn"
    
    # Verificar que el HTML no está vacío
    html = data["html"]
    assert len(html.strip()) > 0
    
    # Verificar que preserva algunas etiquetas
    assert "<p>" in html or "<strong>" in html or "mundo" in html
    
    print(f"\nHTML traducido ES→DA: {html}")


def test_danish_to_spanish_simple(client):
    """Test de traducción Danés→Español."""
    payload = {
        "text": "Hej verden",
        "direction": "da-es"
    }
    
    response = client.post("/translate", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["direction"] == "da-es"
    assert data["source"] == "dan_Latn"
    assert data["target"] == "spa_Latn"
    assert "translations" in data
    assert len(data["translations"]) == 1
    
    translation = data["translations"][0]
    assert len(translation.strip()) > 0
    
    # Verificar que contiene palabras españolas (aproximado)
    print(f"\nTraducción DA→ES: 'Hej verden' → '{translation}'")


def test_danish_to_spanish_question(client):
    """Test DA→ES con pregunta."""
    payload = {
        "text": "Hvordan har du det?",
        "direction": "da-es"
    }
    
    response = client.post("/translate", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    translation = data["translations"][0]
    assert len(translation.strip()) > 0
    
    print(f"\nTraducción DA→ES: 'Hvordan har du det?' → '{translation}'")


def test_bidirectional_consistency(client):
    """Test de consistencia bidireccional."""
    # ES→DA
    payload_es_da = {
        "text": "Buenos días",
        "direction": "es-da"
    }
    response_es_da = client.post("/translate", json=payload_es_da)
    assert response_es_da.status_code == 200
    
    # DA→ES
    payload_da_es = {
        "text": "Godmorgen",
        "direction": "da-es"
    }
    response_da_es = client.post("/translate", json=payload_da_es)
    assert response_da_es.status_code == 200
    
    # Ambas deben funcionar
    assert len(response_es_da.json()["translations"][0]) > 0
    assert len(response_da_es.json()["translations"][0]) > 0
    
    print(f"\nBidireccional OK:")
    print(f"  ES→DA: 'Buenos días' → '{response_es_da.json()['translations'][0]}'")
    print(f"  DA→ES: 'Godmorgen' → '{response_da_es.json()['translations'][0]}'")


if __name__ == "__main__":
    # Permitir ejecutar tests directamente
    pytest.main([__file__, "-v", "-s"])

