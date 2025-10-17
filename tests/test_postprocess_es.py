"""
Tests para post-procesado español (postprocess_es.py).

Verifica normalización de fechas y números al formato español.
"""
import pytest
from app.postprocess_es import (
    normalize_dates_es,
    normalize_numbers_es,
    postprocess_es
)


def test_normalize_dates_dot_to_slash():
    """Test de normalización de fechas danesas a españolas."""
    text = "La reunión es el 16.10.2025"
    result = normalize_dates_es(text)
    
    assert "16/10/2025" in result
    assert "16.10.2025" not in result


def test_normalize_dates_multiple():
    """Test con múltiples fechas."""
    text = "Eventos: 25.12.2025 y 01.01.2026"
    result = normalize_dates_es(text)
    
    assert "25/12/2025" in result
    assert "01/01/2026" in result


def test_postprocess_es_dates():
    """Test de post-procesado completo con fechas."""
    text = "El evento será el 16.10.2025"
    result = postprocess_es(text)
    
    assert "16/10/2025" in result


def test_postprocess_es_preserves_content():
    """Test que el post-procesado no pierde contenido."""
    text = "Dette er en test med dato 01.01.2025 og tal 1234"
    result = postprocess_es(text)
    
    # Debe preservar contenido
    assert "Dette er en test" in result
    assert "1234" in result
    assert "01/01/2025" in result


def test_postprocess_es_empty_text():
    """Test con texto vacío."""
    result = postprocess_es("")
    assert result == ""


def test_normalize_numbers_es():
    """Test de normalización de números."""
    text = "El precio es 1.234,56 EUR"
    result = normalize_numbers_es(text)
    
    # Por ahora, los números se preservan tal cual
    assert "1.234,56" in result or "1234" in result


def test_postprocess_es_no_dates():
    """Test con texto sin fechas."""
    text = "Hola mundo sin fechas"
    result = postprocess_es(text)
    
    # Debe preservar el texto tal cual
    assert "Hola mundo sin fechas" in result


def test_postprocess_es_mixed_content():
    """Test con contenido mixto."""
    text = "Møde den 16.10.2025 kl. 14:00"
    result = postprocess_es(text)
    
    # Fecha debe estar normalizada
    assert "16/10/2025" in result
    # Resto del contenido debe estar
    assert "Møde" in result
    assert "14:00" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

