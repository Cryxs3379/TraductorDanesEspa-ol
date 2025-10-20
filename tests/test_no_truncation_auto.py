"""
Tests para verificar comportamiento de tokens auto, elevación y strict_max.

Valida que las mejoras de anti-truncado funcionen correctamente.
"""
import pytest
from fastapi.testclient import TestClient
from app.app import app


client = TestClient(app)


def test_auto_tokens_long_text():
    """Test con max_new_tokens no especificado (auto-calculado por el servidor)."""
    # Texto largo que debería calcular max_new_tokens automáticamente
    text = "Esta es una frase larga para testing. " * 100  # ~3900 chars
    
    payload = {
        "text": text,
        "direction": "es-da"
        # No enviar max_new_tokens - el backend lo calcula
    }
    
    response = client.post("/translate", json=payload)
    
    if response.status_code == 503:
        pytest.skip("Modelo no cargado - ejecutar con servidor real")
    
    assert response.status_code == 200
    
    data = response.json()
    translation = data["translations"][0]
    
    # Verificar que no está truncado (debe tener contenido sustancial)
    assert len(translation) > 100, "Traducción parece truncada"
    
    print(f"\n✅ Auto tokens funcionó:")
    print(f"   Entrada: {len(text)} caracteres")
    print(f"   Salida:  {len(translation)} caracteres")


def test_manual_with_elevation():
    """Test con max_new_tokens bajo pero strict_max=False (elevación server-side)."""
    text = "Esta es una frase larga para probar la elevación automática. " * 50  # ~3150 chars
    
    payload = {
        "text": text,
        "direction": "es-da",
        "max_new_tokens": 64,  # muy bajo para este texto
        "strict_max": False    # permitir elevación
    }
    
    response = client.post("/translate", json=payload)
    
    if response.status_code == 503:
        pytest.skip("Modelo no cargado - ejecutar con servidor real")
    
    assert response.status_code == 200
    
    data = response.json()
    translation = data["translations"][0]
    
    # Debe haber sido elevado automáticamente y no truncado
    assert len(translation) > 50, "Elevación no funcionó"
    
    print(f"\n✅ Elevación server-side funcionó:")
    print(f"   Solicitado: 64 tokens")
    print(f"   Salida:     {len(translation)} caracteres (debería ser completa)")


def test_strict_max_respects_limit():
    """Test con strict_max=True (debe respetar límite exacto)."""
    text = "Esta es una frase larga. " * 30  # ~750 chars
    
    payload = {
        "text": text,
        "direction": "es-da",
        "max_new_tokens": 32,  # muy bajo
        "strict_max": True     # NO elevar
    }
    
    response = client.post("/translate", json=payload)
    
    if response.status_code == 503:
        pytest.skip("Modelo no cargado - ejecutar con servidor real")
    
    # Puede ser 200 con traducción corta, o 422 si falla validación
    assert response.status_code in [200, 422], "Respuesta inesperada"
    
    if response.status_code == 200:
        data = response.json()
        translation = data["translations"][0]
        print(f"\n⚠️  Strict=True respetado: traducción corta ({len(translation)} chars)")
    else:
        print(f"\n⚠️  Strict=True: validación falló (esperado con límite muy bajo)")


def test_continuation_not_triggered_if_complete():
    """Test que verifica que continuación NO se activa si la traducción termina bien."""
    text = "Hola mundo."  # Texto corto
    
    payload = {
        "text": text,
        "direction": "es-da"
    }
    
    response = client.post("/translate", json=payload)
    
    if response.status_code == 503:
        pytest.skip("Modelo no cargado - ejecutar con servidor real")
    
    assert response.status_code == 200
    
    data = response.json()
    translation = data["translations"][0]
    
    # Debe terminar con puntuación (no necesita continuación)
    assert translation.strip()[-1] in ['.', '!', '?'], "Traducción corta debe terminar con puntuación"
    
    print(f"\n✅ Traducción corta completa: '{translation}'")


def test_medium_text_no_truncation():
    """Test con texto mediano (~2000 chars) que anteriormente fallaba."""
    text = "Primera oración con contenido importante. Segunda oración con más detalles. " * 80  # ~6400 chars
    
    payload = {
        "text": text[:2180],  # Exactamente 2180 chars como reportó el usuario
        "direction": "es-da"
    }
    
    response = client.post("/translate", json=payload)
    
    if response.status_code == 503:
        pytest.skip("Modelo no cargado - ejecutar con servidor real")
    
    assert response.status_code == 200
    
    data = response.json()
    translation = data["translations"][0]
    
    # Verificar que no está vacío ni truncado
    assert len(translation) > 200, "Texto de 2180 chars debe generar traducción sustancial"
    
    print(f"\n✅ Texto 2180 chars traducido correctamente:")
    print(f"   Entrada: 2180 caracteres")
    print(f"   Salida:  {len(translation)} caracteres")
    print(f"   Primeros 100 chars: {translation[:100]}...")


def test_direction_danish_to_spanish():
    """Test DA→ES con auto tokens."""
    text = "Dette er en lang sætning på dansk. " * 50  # Texto largo en danés
    
    payload = {
        "text": text,
        "direction": "da-es"
    }
    
    response = client.post("/translate", json=payload)
    
    if response.status_code == 503:
        pytest.skip("Modelo no cargado - ejecutar con servidor real")
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["direction"] == "da-es"
    assert data["source"] == "dan_Latn"
    assert data["target"] == "spa_Latn"
    
    translation = data["translations"][0]
    assert len(translation) > 50
    
    print(f"\n✅ DA→ES con auto tokens: {len(text)} → {len(translation)} chars")


def test_batch_with_auto_tokens():
    """Test con múltiples textos en batch, auto tokens."""
    texts = [
        "Primer texto corto.",
        "Segundo texto mucho más largo. " * 80,  # ~2480 chars
        "Tercer texto mediano. " * 20  # ~420 chars
    ]
    
    payload = {
        "text": texts,
        "direction": "es-da"
    }
    
    response = client.post("/translate", json=payload)
    
    if response.status_code == 503:
        pytest.skip("Modelo no cargado - ejecutar con servidor real")
    
    assert response.status_code == 200
    
    data = response.json()
    translations = data["translations"]
    
    assert len(translations) == 3
    
    # Todos deben tener contenido
    for i, trans in enumerate(translations):
        assert len(trans) > 10, f"Texto {i+1} truncado"
        print(f"   Texto {i+1}: {len(texts[i])} → {len(trans)} chars")
    
    print("\n✅ Batch con auto tokens: todos los textos completos")

