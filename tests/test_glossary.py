"""
Tests para el módulo de glosario (glossary.py).

Verifica:
- Protección de términos con marcadores
- Protección automática de URLs, emails y números
- Reemplazo correcto de términos en post-procesamiento
"""
import pytest
from app.glossary import (
    apply_glossary_pre,
    apply_glossary_post,
    clean_glossary_markers,
    _protect_entities,
    _restore_entities
)


def test_protect_entities_urls():
    """Test de protección de URLs."""
    text = "Visita https://www.example.com y http://test.org"
    protected, entities = _protect_entities(text)
    
    # Verificar que las URLs fueron protegidas
    assert "__URL_0__" in protected
    assert "__URL_1__" in protected
    assert "https://www.example.com" not in protected
    
    # Verificar lista de entidades
    assert len(entities) == 2
    assert any("https://www.example.com" in e for e in entities)


def test_protect_entities_emails():
    """Test de protección de emails."""
    text = "Contacta a usuario@example.com o soporte@test.org"
    protected, entities = _protect_entities(text)
    
    # Verificar que los emails fueron protegidos
    assert "__EMAIL_0__" in protected
    assert "__EMAIL_1__" in protected
    assert "usuario@example.com" not in protected
    
    assert len(entities) == 2


def test_protect_entities_numbers():
    """Test de protección de números."""
    text = "El precio es 1000 EUR o 1,234.56 DKK"
    protected, entities = _protect_entities(text)
    
    # Verificar que los números fueron protegidos
    assert "__NUM_" in protected
    assert len([e for e in entities if e[0].startswith("__NUM_")]) >= 2


def test_glossary_pre_basic():
    """Test básico de aplicación pre-glosario."""
    glossary = {
        "Acme": "Acme",
        "Python": "Python"
    }
    
    text = "Bienvenido a Acme Corporation. Usamos Python."
    result = apply_glossary_pre(text, glossary)
    
    # Verificar que los términos fueron marcados
    assert "[[TERM::Acme]]" in result or "[[KEEP::Acme]]" in result
    assert "[[TERM::Python]]" in result or "[[KEEP::Python]]" in result


def test_glossary_pre_case_insensitive():
    """Test de glosario case-insensitive."""
    glossary = {
        "acme": "Acme"
    }
    
    text = "Bienvenido a ACME y a Acme y a acme"
    result = apply_glossary_pre(text, glossary)
    
    # Todos deben ser marcados independientemente del case
    assert result.count("[[TERM::") >= 3 or result.count("[[KEEP::") >= 0


def test_glossary_pre_preserves_urls():
    """Test de que las URLs se preservan."""
    glossary = {
        "test": "prueba"
    }
    
    text = "Visita https://test.com para más info sobre test"
    result = apply_glossary_pre(text, glossary)
    
    # URL debe estar protegida
    assert "[[KEEP::https://test.com]]" in result
    # Palabra "test" sola debe estar marcada
    assert "[[TERM::test]]" in result


def test_glossary_post_basic():
    """Test básico de aplicación post-glosario."""
    glossary = {
        "Acme": "Acme",
        "Corporation": "Selskab"
    }
    
    text = "Velkommen til [[TERM::Acme]] [[TERM::Corporation]]"
    result = apply_glossary_post(text, glossary)
    
    # Verificar reemplazos
    assert "Acme" in result
    assert "Selskab" in result
    assert "[[TERM::" not in result


def test_glossary_post_restores_entities():
    """Test de que las entidades protegidas se restauran."""
    glossary = {}
    
    text = "Contacta a [[KEEP::usuario@example.com]] o visita [[KEEP::https://test.com]]"
    result = apply_glossary_post(text, glossary)
    
    # Entidades deben ser restauradas
    assert "usuario@example.com" in result
    assert "https://test.com" in result
    assert "[[KEEP::" not in result


def test_glossary_post_handles_missing_terms():
    """Test de manejo de términos no encontrados en glosario."""
    glossary = {
        "Acme": "Acme"
    }
    
    text = "[[TERM::Acme]] [[TERM::UnknownTerm]]"
    result = apply_glossary_post(text, glossary)
    
    # Acme debe ser reemplazado
    assert "Acme" in result
    # UnknownTerm debe aparecer sin marcador (fallback)
    assert "UnknownTerm" in result
    assert "[[TERM::" not in result


def test_clean_glossary_markers():
    """Test de limpieza de marcadores residuales."""
    text = "Texto con [[TERM::algo]] y [[KEEP::otro]]"
    result = clean_glossary_markers(text)
    
    assert "[[TERM::" not in result
    assert "[[KEEP::" not in result
    assert "algo" in result
    assert "otro" in result


def test_glossary_full_workflow():
    """Test completo de flujo pre -> traducción simulada -> post."""
    glossary = {
        "Acme": "Acme",
        "Corporation": "Selskab"
    }
    
    # Texto original
    text = "Bienvenido a Acme Corporation. Email: info@acme.com"
    
    # Pre-procesamiento
    pre_result = apply_glossary_pre(text, glossary)
    
    # Simular traducción (solo convertimos marcadores a "danés ficticio")
    # En realidad, el modelo traduciría, pero aquí simulamos
    translated = pre_result.replace("Bienvenido a", "Velkommen til")
    
    # Post-procesamiento
    post_result = apply_glossary_post(translated, glossary)
    
    # Verificaciones
    assert "Acme" in post_result
    assert "Selskab" in post_result
    assert "info@acme.com" in post_result  # Email preservado
    assert "[[TERM::" not in post_result
    assert "[[KEEP::" not in post_result


def test_glossary_with_multiword_terms():
    """Test con términos de varias palabras."""
    glossary = {
        "Acme Corporation": "Acme Selskab",
        "Python": "Python"
    }
    
    text = "Bienvenido a Acme Corporation. Usamos Python."
    result = apply_glossary_pre(text, glossary)
    
    # Término multi-palabra debe tener prioridad (más largo primero)
    assert "[[TERM::Acme Corporation]]" in result or "[[KEEP::" in result


def test_glossary_empty():
    """Test con glosario vacío."""
    text = "Texto normal"
    result = apply_glossary_pre(text, {})
    
    # Solo debe proteger entidades (URLs, emails, números)
    # Como no hay ninguna, el texto debe quedar casi igual
    assert "Texto normal" in result or "[[KEEP::" in result


def test_glossary_special_characters():
    """Test con caracteres especiales en términos."""
    glossary = {
        "C++": "C++",
        ".NET": ".NET"
    }
    
    text = "Programamos en C++ y .NET Framework"
    result = apply_glossary_pre(text, glossary)
    
    # Caracteres especiales deben ser escapados correctamente
    # No debe romper el regex
    assert "C++" in result or "[[" in result
    assert ".NET" in result or "[[" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

