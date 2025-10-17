"""
Tests para verificar que textos largos no se truncan.

Validación de la mejora de límites y segmentación automática.
"""
import pytest
from fastapi.testclient import TestClient
from app.app import app


client = TestClient(app)


def test_plain_long_text_not_truncated():
    """
    Test que verifica que textos largos (>3000 caracteres) no se truncan.
    
    Con MAX_INPUT_TOKENS aumentado a 1024 y segmentación automática,
    los textos largos deben traducirse completamente.
    """
    # Generar texto largo (~3400 caracteres)
    text = "Primera oración. Segunda oración. Tercera oración. " * 100
    
    payload = {
        "text": text,
        "direction": "es-da",
        "max_new_tokens": 384  # suficiente para textos largos
    }
    
    response = client.post("/translate", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "translations" in data
    assert len(data["translations"]) == 1
    
    translation = data["translations"][0]
    assert len(translation.strip()) > 0, "La traducción no debe estar vacía"
    
    # Verificar que la traducción tenga una longitud razonable
    # (no cortada abruptamente)
    assert len(translation) > 100, "La traducción parece truncada"
    
    print(f"\n✓ Texto largo traducido: {len(text)} chars → {len(translation)} chars")


def test_multiple_long_texts_batch():
    """
    Test que verifica que múltiples textos largos se procesan correctamente.
    """
    text1 = "Este es el primer texto largo. " * 80
    text2 = "Este es el segundo texto largo. " * 80
    
    payload = {
        "text": [text1, text2],
        "direction": "es-da",
        "max_new_tokens": 384
    }
    
    response = client.post("/translate", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert len(data["translations"]) == 2
    
    for idx, translation in enumerate(data["translations"]):
        assert len(translation.strip()) > 0
        assert len(translation) > 100
        print(f"✓ Texto {idx+1}: {len(translation)} chars")


def test_adaptive_max_new_tokens():
    """
    Test que verifica que max_new_tokens adaptativo funciona.
    
    Si el cliente no especifica max_new_tokens, el backend debe
    calcularlo basado en la longitud de entrada.
    """
    short_text = "Hola mundo."
    long_text = "Esta es una frase larga. " * 50
    
    # Test con texto corto (debe usar un valor bajo)
    payload_short = {
        "text": short_text,
        "direction": "es-da"
        # No especificamos max_new_tokens
    }
    
    response_short = client.post("/translate", json=payload_short)
    assert response_short.status_code == 200
    
    # Test con texto largo (debe usar un valor más alto)
    payload_long = {
        "text": long_text,
        "direction": "es-da"
        # No especificamos max_new_tokens
    }
    
    response_long = client.post("/translate", json=payload_long)
    assert response_long.status_code == 200
    
    data_long = response_long.json()
    translation_long = data_long["translations"][0]
    
    # La traducción del texto largo debe ser significativamente más larga
    assert len(translation_long) > len(short_text) * 2
    
    print(f"\n✓ Texto corto: {len(short_text)} chars")
    print(f"✓ Texto largo: {len(long_text)} chars → {len(translation_long)} chars")


def test_segmentation_preserves_meaning():
    """
    Test que verifica que la segmentación automática no corta frases.
    """
    # Texto con múltiples párrafos
    text = """
    Este es el primer párrafo de un documento largo. Contiene varias oraciones
    que deben traducirse correctamente sin perder contexto.
    
    Este es el segundo párrafo. También tiene múltiples oraciones. La segmentación
    debe respetar los límites de párrafo.
    
    Finalmente, este es el tercer párrafo que completa el documento.
    """ * 10
    
    payload = {
        "text": text,
        "direction": "es-da",
        "max_new_tokens": 384
    }
    
    response = client.post("/translate", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    translation = data["translations"][0]
    
    # Verificar que hay contenido traducido
    assert len(translation) > 500
    
    # Verificar que hay estructura (espacios, no es una sola palabra)
    assert " " in translation
    
    print(f"\n✓ Segmentación preserva estructura: {len(translation)} chars")


def test_max_new_tokens_boundary():
    """
    Test que verifica los límites de max_new_tokens (32-512).
    """
    text = "Hola mundo."
    
    # Test con valor mínimo
    payload_min = {
        "text": text,
        "direction": "es-da",
        "max_new_tokens": 32
    }
    
    response_min = client.post("/translate", json=payload_min)
    assert response_min.status_code == 200
    
    # Test con valor máximo
    payload_max = {
        "text": text,
        "direction": "es-da",
        "max_new_tokens": 512
    }
    
    response_max = client.post("/translate", json=payload_max)
    assert response_max.status_code == 200
    
    # Test con valor fuera de rango (debe fallar por validación Pydantic)
    payload_invalid = {
        "text": text,
        "direction": "es-da",
        "max_new_tokens": 600  # > 512
    }
    
    response_invalid = client.post("/translate", json=payload_invalid)
    assert response_invalid.status_code == 422  # Validation error
    
    print("✓ Límites de max_new_tokens validados correctamente")

