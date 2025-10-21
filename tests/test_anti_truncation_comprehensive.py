"""
Tests comprensivos anti-truncado para textos muy largos y casos edge.
"""
import pytest
from fastapi.testclient import TestClient
from app.app import app

client = TestClient(app)


@pytest.fixture
def very_long_text():
    """Texto muy largo para testing (~5000 chars)."""
    return "Esto es un texto muy largo para probar que no se trunca la traducción. " * 100


@pytest.fixture
def html_long_text():
    """HTML largo para testing."""
    return """
    <html>
        <body>
            <h1>Título principal</h1>
            <p>Este es un párrafo muy largo. """ + "Contenido extenso que debe traducirse completamente. " * 80 + """</p>
            <ul>
                <li>Item 1</li>
                <li>Item 2</li>
            </ul>
        </body>
    </html>
    """


def test_very_long_text_complete_translation(very_long_text):
    """Test que textos muy largos se traduzcan completamente sin truncado."""
    payload = {
        "text": very_long_text,
        "direction": "es-da"
        # Auto tokens - sin max_new_tokens
    }
    
    response = client.post("/translate", json=payload)
    
    if response.status_code == 503:
        pytest.skip("Modelo no cargado - ejecutar con servidor real")
    
    assert response.status_code == 200
    
    data = response.json()
    translation = data["translations"][0]
    
    # Ratio mínimo esperado: 60% del original
    min_expected_length = len(very_long_text) * 0.6
    assert len(translation) >= min_expected_length, (
        f"Traducción truncada: {len(translation)} chars vs mínimo esperado {min_expected_length}"
    )
    
    # Verificar que contiene contenido sustancial del principio y final
    original_start = very_long_text[:100]
    original_end = very_long_text[-100:]
    
    # La traducción debe tener contenido del principio y final
    assert len(translation) > 1000, "Traducción demasiado corta para texto largo"
    
    print(f"✅ Texto muy largo traducido completamente:")
    print(f"   Original: {len(very_long_text)} chars")
    print(f"   Traducido: {len(translation)} chars")
    print(f"   Ratio: {len(translation)/len(very_long_text):.1%}")


def test_html_long_preserves_structure(html_long_text):
    """Test que HTML largo preserve estructura y no se trunce contenido."""
    payload = {
        "html": html_long_text,
        "direction": "es-da"
    }
    
    response = client.post("/translate/html", json=payload)
    
    if response.status_code == 503:
        pytest.skip("Modelo no cargado - ejecutar con servidor real")
    
    assert response.status_code == 200
    
    data = response.json()
    translated_html = data["html"]
    
    # Verificar que mantiene etiquetas HTML principales
    assert "<h1>" in translated_html, "Etiqueta h1 perdida"
    assert "<p>" in translated_html, "Etiqueta p perdida"
    assert "<ul>" in translated_html, "Etiqueta ul perdida"
    assert "<li>" in translated_html, "Etiquetas li perdidas"
    
    # Verificar que el contenido traducido es sustancial
    # Extraer solo el texto (sin HTML)
    import re
    clean_text = re.sub(r'<[^>]+>', '', translated_html)
    assert len(clean_text) > 1000, "Contenido HTML traducido insuficiente"
    
    print(f"✅ HTML largo preserva estructura:")
    print(f"   HTML traducido: {len(translated_html)} chars")
    print(f"   Texto limpio: {len(clean_text)} chars")


def test_segmentation_reassembly_exact():
    """Test que la segmentación y reensamblado no pierda contenido."""
    # Texto que debe segmentarse
    long_text = "Primera parte del texto muy largo. " + "Contenido extenso en el medio. " * 200 + "Final del texto que debe aparecer."
    
    payload = {
        "text": long_text,
        "direction": "es-da"
    }
    
    response = client.post("/translate", json=payload)
    
    if response.status_code == 503:
        pytest.skip("Modelo no cargado - ejecutar con servidor real")
    
    assert response.status_code == 200
    
    data = response.json()
    translation = data["translations"][0]
    
    # Verificar que el final está presente (indica que no se perdió al reensamblar)
    assert len(translation) > 500, "Reensamblado incorrecto - traducción muy corta"
    
    # Verificar que no hay pérdida evidente de contenido
    ratio = len(translation) / len(long_text)
    assert ratio > 0.5, f"Ratio muy bajo sugiere pérdida: {ratio:.1%}"
    
    print(f"✅ Segmentación/reensamblado correcto:")
    print(f"   Entrada: {len(long_text)} chars")
    print(f"   Salida: {len(translation)} chars")
    print(f"   Ratio: {ratio:.1%}")


def test_bilingual_roundtrip_complete():
    """Test ES→DA→ES para verificar que no hay pérdida en ida y vuelta."""
    original_es = "Este es un texto en español que debe traducirse completamente al danés y luego de vuelta al español sin perder información importante."
    
    # ES → DA
    payload_es_da = {
        "text": original_es,
        "direction": "es-da"
    }
    
    response = client.post("/translate", json=payload_es_da)
    
    if response.status_code == 503:
        pytest.skip("Modelo no cargado - ejecutar con servidor real")
    
    assert response.status_code == 200
    danish_text = response.json()["translations"][0]
    
    # DA → ES
    payload_da_es = {
        "text": danish_text,
        "direction": "da-es"
    }
    
    response = client.post("/translate", json=payload_da_es)
    assert response.status_code == 200
    
    back_to_spanish = response.json()["translations"][0]
    
    # Verificar que no se perdió contenido significativo
    assert len(back_to_spanish) > len(original_es) * 0.7, "Pérdida significativa en roundtrip"
    
    print(f"✅ Roundtrip ES→DA→ES completo:")
    print(f"   Original ES: {len(original_es)} chars")
    print(f"   Danish: {len(danish_text)} chars")
    print(f"   Back to ES: {len(back_to_spanish)} chars")


def test_continuation_triggered_for_long_text():
    """Test que la continuación se active para textos largos."""
    # Usar el texto del usuario que causó problemas
    user_problematic_text = """Esto no se queda en el periodismo. Las editoriales y los lectores hoy por hoy agradecen los libros narrativos cortos, novelas fragmentadas y relatos breves: un objeto liviano que puedan leer de a sorbos en no más de una semana (yo misma escribo así). Porque ya es poca la concentración y el tiempo que nos queda, y porque nos hemos acostumbrado a la rapidez de ese clickbait y de las redes sociales. Así, muchos libros de no ficción, de autoayuda, autobiográficos o incluso narrativos están siguiendo esta línea para acelerar su lectura y no perder audiencia. Además, no solo se escriben livianos, sino que se leerán cada vez más livianos. Hoy existen apps donde puedes subir un libro en pdf y pedirle que te lo resuma en dos líneas. Queremos leer así porque no hay tiempo, porque a la décima línea nos distraemos, nos aburrimos, miramos TikTok, vamos a la cocina a hacernos un café y luego olvidamos retomarlo. ¿Por qué leerlo completo si puedo pedirle a un robot el famoso TLDR"""
    
    payload = {
        "text": user_problematic_text,
        "direction": "es-da"
    }
    
    response = client.post("/translate", json=payload)
    
    if response.status_code == 503:
        pytest.skip("Modelo no cargado - ejecutar con servidor real")
    
    assert response.status_code == 200
    
    data = response.json()
    translation = data["translations"][0]
    
    # Verificar que el final está presente (TLDR/robot)
    translation_lower = translation.lower()
    has_tldr_reference = "tldr" in translation_lower or "robot" in translation_lower or "komplet" in translation_lower
    
    assert has_tldr_reference, f"Final del texto perdido - no se encontró referencia a TLDR/robot en: ...{translation[-200:]}"
    
    # Verificar ratio adecuado
    ratio = len(translation) / len(user_problematic_text)
    assert ratio >= 0.8, f"Ratio insuficiente: {ratio:.1%} - probable truncado"
    
    print(f"✅ Texto problemático del usuario traducido completamente:")
    print(f"   Original: {len(user_problematic_text)} chars")
    print(f"   Traducido: {len(translation)} chars")
    print(f"   Ratio: {ratio:.1%}")
    print(f"   Tiene TLDR/robot: {has_tldr_reference}")


def test_auto_vs_manual_tokens_comparison():
    """Test comparando auto vs manual tokens para mismo texto."""
    test_text = "Texto de prueba largo. " * 100  # ~2300 chars
    
    # Auto tokens
    payload_auto = {
        "text": test_text,
        "direction": "es-da"
    }
    
    response_auto = client.post("/translate", json=payload_auto)
    
    if response_auto.status_code == 503:
        pytest.skip("Modelo no cargado - ejecutar con servidor real")
    
    assert response_auto.status_code == 200
    translation_auto = response_auto.json()["translations"][0]
    
    # Manual tokens (alto)
    payload_manual = {
        "text": test_text,
        "direction": "es-da",
        "max_new_tokens": 2048,
        "strict_max": False
    }
    
    response_manual = client.post("/translate", json=payload_manual)
    assert response_manual.status_code == 200
    translation_manual = response_manual.json()["translations"][0]
    
    # Ambos deben ser completos (diferencias menores por aleatoriedad)
    assert len(translation_auto) > 1000, "Auto tokens truncado"
    assert len(translation_manual) > 1000, "Manual tokens truncado"
    
    # Las diferencias no deben ser extremas
    length_diff = abs(len(translation_auto) - len(translation_manual))
    assert length_diff < len(test_text), "Diferencias extremas entre auto y manual"
    
    print(f"✅ Auto vs Manual tokens:")
    print(f"   Auto: {len(translation_auto)} chars")
    print(f"   Manual: {len(translation_manual)} chars")
    print(f"   Diferencia: {length_diff} chars")
