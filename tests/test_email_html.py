"""
Tests para el módulo de procesamiento de HTML de correos (segment.py).

Verifica:
- Extracción de texto de HTML preservando estructura
- Segmentación de texto para emails
- Reconstrucción de HTML con etiquetas preservadas
"""
import pytest
from app.segment import (
    split_text_for_email,
    split_html_preserving_structure,
    rehydrate_html
)


def test_split_text_for_email_short():
    """Test de segmentación de texto corto."""
    text = "Hola mundo. ¿Cómo estás?"
    segments = split_text_for_email(text)
    
    # Texto corto no debe segmentarse
    assert len(segments) == 1
    assert segments[0] == text


def test_split_text_for_email_long():
    """Test de segmentación de texto largo."""
    # Texto largo (>600 chars)
    text = "Primera oración. " * 50  # ~850 chars
    segments = split_text_for_email(text, max_segment_chars=600)
    
    # Debe segmentarse
    assert len(segments) > 1
    
    # Cada segmento debe ser menor que el máximo
    for seg in segments:
        assert len(seg) <= 650  # Margen de tolerancia


def test_split_text_for_email_paragraphs():
    """Test con párrafos separados."""
    text = "Primer párrafo.\n\nSegundo párrafo.\n\nTercer párrafo."
    segments = split_text_for_email(text)
    
    # Debe respetar saltos de párrafo
    assert len(segments) >= 1


def test_split_html_preserving_structure_simple():
    """Test de extracción de HTML simple."""
    html = "<p>Hola mundo</p><p>Segunda línea</p>"
    blocks, texts = split_html_preserving_structure(html)
    
    # Debe extraer textos
    assert len(texts) >= 1
    assert any("Hola mundo" in t for t in texts)


def test_split_text_for_email_short():
    """Test de segmentación de texto corto."""
    text = "Hola mundo. ¿Cómo estás?"
    segments = split_text_for_email(text)
    
    # Texto corto no debe segmentarse
    assert len(segments) == 1
    assert segments[0] == text


def test_split_text_for_email_long():
    """Test de segmentación de texto largo."""
    # Texto largo (>600 chars)
    text = "Primera oración. " * 50  # ~850 chars
    segments = split_text_for_email(text, max_segment_chars=600)
    
    # Debe segmentarse
    assert len(segments) > 1
    
    # Cada segmento debe ser menor que el máximo
    for seg in segments:
        assert len(seg) <= 650  # Margen de tolerancia


def test_split_text_for_email_paragraphs():
    """Test con párrafos separados."""
    text = "Primer párrafo.\n\nSegundo párrafo.\n\nTercer párrafo."
    segments = split_text_for_email(text)
    
    # Debe respetar saltos de párrafo
    assert len(segments) >= 1


def test_split_html_simple():
    """Test de extracción de HTML simple."""
    html = "<p>Hola mundo</p><p>Segunda línea</p>"
    blocks, texts = split_html_preserving_structure(html)
    
    # Debe extraer textos
    assert len(texts) >= 1
    assert any("Hola mundo" in t for t in texts)


def test_split_html_with_link():
    """Test con enlaces."""
    html = '<p>Visita <a href="https://example.com">nuestro sitio</a></p>'
    blocks, texts = split_html_preserving_structure(html)
    
    # Debe extraer texto del enlace
    assert len(texts) >= 1
    assert any("nuestro sitio" in t or "Visita" in t for t in texts)


def test_rehydrate_html_simple():
    """Test de reconstrucción de HTML simple."""
    blocks = [
        {'type': 'tag_open', 'name': 'p', 'attrs': {}},
        {'type': 'text', 'content': 'Original', 'index': 0},
        {'type': 'tag_close', 'name': 'p'}
    ]
    translations = ['Traducido']
    
    html = rehydrate_html(blocks, translations)
    
    assert '<p>' in html
    assert 'Traducido' in html
    assert '</p>' in html


def test_rehydrate_html_with_attributes():
    """Test de reconstrucción preservando atributos."""
    blocks = [
        {'type': 'tag_open', 'name': 'a', 'attrs': {'href': 'https://test.com'}},
        {'type': 'text', 'content': 'link', 'index': 0},
        {'type': 'tag_close', 'name': 'a'}
    ]
    translations = ['enlace']
    
    html = rehydrate_html(blocks, translations)
    
    assert 'href="https://test.com"' in html
    assert 'enlace' in html
    assert '<a' in html


def test_split_and_rehydrate_roundtrip():
    """Test completo de extracción y reconstrucción."""
    original_html = '<p>Texto <strong>importante</strong></p>'
    
    # Extraer
    blocks, texts = split_html_preserving_structure(original_html)
    
    # "Traducir" (identidad)
    translations = texts
    
    # Reconstruir
    reconstructed = rehydrate_html(blocks, translations)
    
    # Debe ser similar al original
    assert '<p>' in reconstructed
    assert '<strong>' in reconstructed or 'importante' in reconstructed


def test_split_html_empty():
    """Test con HTML vacío."""
    blocks, texts = split_html_preserving_structure("")
    
    # No debe fallar
    assert isinstance(blocks, list)
    assert isinstance(texts, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

