"""
Tests para post-procesado danés (postprocess_da.py).

Verifica normalización de números, fechas y formalización.
"""
import pytest
from app.postprocess_da import (
    normalize_numbers_da,
    normalize_dates_da,
    formalize_da,
    postprocess_da
)


def test_normalize_dates_slash_to_dot():
    """Test de normalización de fechas con slashes."""
    text = "La reunión es el 16/10/2025"
    result = normalize_dates_da(text)
    
    assert "16.10.2025" in result
    assert "16/10/2025" not in result


def test_normalize_dates_hyphen_to_dot():
    """Test de normalización de fechas con guiones."""
    text = "El evento será el 25-12-2025"
    result = normalize_dates_da(text)
    
    assert "25.12.2025" in result
    assert "25-12-2025" not in result


def test_formalize_da_greeting():
    """Test de formalización de saludo."""
    text = "Hej Pedro"
    result = formalize_da(text)
    
    # "Hej" debe convertirse en "Kære" (estimado)
    assert "Kære" in result
    assert "Hej" not in result


def test_formalize_da_closing():
    """Test de formalización de despedida."""
    text = "Gracias. Hilsen"
    result = formalize_da(text)
    
    # "Hilsen" debe convertirse en "Med venlig hilsen"
    assert "Med venlig hilsen" in result


def test_formalize_da_you_to_formal():
    """Test de conversión de tuteo a formal."""
    text = "Kan du hjælpe mig?"  # ¿Puedes ayudarme?
    result = formalize_da(text)
    
    # "du" debe convertirse en "De" (usted)
    assert "De" in result or "de" in result


def test_postprocess_da_no_formal():
    """Test de post-procesado sin formalización."""
    text = "Hej verden. Mødet er den 16/10/2025"
    result = postprocess_da(text, formal=False)
    
    # Debe normalizar fecha pero NO formalizar saludo
    assert "16.10.2025" in result
    assert "Hej" in result  # No cambia sin formal=True


def test_postprocess_da_with_formal():
    """Test de post-procesado con formalización."""
    text = "Hej kunde. Kan du kontakte os?"
    result = postprocess_da(text, formal=True)
    
    # Debe formalizar
    assert "Kære" in result
    assert "De" in result or "de" in result


def test_postprocess_da_preserves_content():
    """Test que el post-procesado no pierde contenido."""
    text = "Dette er en test med tal 1234 og dato 01/01/2025"
    result = postprocess_da(text, formal=False)
    
    # Debe preservar contenido
    assert "Dette er en test" in result
    assert "1234" in result
    assert "01.01.2025" in result


def test_postprocess_da_empty_text():
    """Test con texto vacío."""
    result = postprocess_da("", formal=False)
    assert result == ""


def test_normalize_numbers_da():
    """Test de normalización de números."""
    # Por ahora, los números se dejan como están
    text = "El precio es 1.234,56 EUR"
    result = normalize_numbers_da(text)
    
    # Debe preservar números
    assert "1.234,56" in result or "1234" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

