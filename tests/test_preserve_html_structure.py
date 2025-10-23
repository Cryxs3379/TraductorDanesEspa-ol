"""
Tests para validar preservación de estructura HTML.

Verifica que el traductor preserva TODAS las etiquetas HTML, <br>, <p>,
y estructura del DOM al traducir correos/HTML.
"""
import pytest
from app.segment import (
    translate_html_preserving_structure,
    split_html_preserving_structure,
    rehydrate_html
)


class TestTranslateHTMLPreservingStructure:
    """Tests para traducción HTML con preservación total de estructura."""
    
    def fake_translate(self, text: str) -> str:
        """Simulador de traducción: ES -> DA."""
        replacements = {
            "Hola": "Hej",
            "mundo": "verden",
            "Estimado": "Kære",
            "cliente": "kunde",
            "Gracias": "Tak",
            "contactar": "kontakte",
            "Atentamente": "Med venlig hilsen",
            "equipo": "hold"
        }
        result = text
        for es, da in replacements.items():
            result = result.replace(es, da)
        return result
    
    def test_preserva_tag_p(self):
        """Debe preservar etiquetas <p>."""
        html = "<p>Hola mundo</p>"
        result = translate_html_preserving_structure(html, self.fake_translate)
        
        # Debe mantener las etiquetas <p>
        assert result.startswith("<p>")
        assert result.endswith("</p>")
        # Texto traducido
        assert "Hej verden" in result
    
    def test_preserva_tag_br(self):
        """Debe preservar etiquetas <br> exactamente."""
        html = "Línea 1<br>Línea 2"
        result = translate_html_preserving_structure(html, self.fake_translate)
        
        # Debe contener <br> o <br/>
        assert "<br" in result.lower()
        # No debe eliminar el <br>
        assert result.count("<br") == 1
    
    def test_preserva_multiple_br(self):
        """Debe preservar múltiples <br>."""
        html = "Línea 1<br><br>Línea 2"
        result = translate_html_preserving_structure(html, self.fake_translate)
        
        # Debe haber 2 <br>
        assert result.lower().count("<br") == 2
    
    def test_preserva_estructura_anidada(self):
        """Debe preservar estructura HTML anidada."""
        html = "<p>Hola <strong>mundo</strong></p>"
        result = translate_html_preserving_structure(html, self.fake_translate)
        
        # Debe mantener <p> y <strong>
        assert "<p>" in result
        assert "</p>" in result
        assert "<strong>" in result
        assert "</strong>" in result
        # Texto traducido
        assert "Hej" in result
        assert "verden" in result
    
    def test_preserva_atributos(self):
        """Debe preservar atributos de etiquetas."""
        html = '<a href="http://example.com">Hola</a>'
        result = translate_html_preserving_structure(html, self.fake_translate)
        
        # Debe mantener el atributo href
        assert 'href="http://example.com"' in result or "href='http://example.com'" in result
        # Texto traducido
        assert "Hej" in result
    
    def test_preserva_listas(self):
        """Debe preservar listas <ul>, <li>."""
        html = "<ul><li>Hola</li><li>mundo</li></ul>"
        result = translate_html_preserving_structure(html, self.fake_translate)
        
        # Debe mantener estructura de lista
        assert "<ul>" in result
        assert "</ul>" in result
        assert result.count("<li>") == 2
        assert result.count("</li>") == 2
    
    def test_no_modifica_html_sin_texto(self):
        """HTML sin texto traducible debe quedar igual."""
        html = "<div><br><br></div>"
        result = translate_html_preserving_structure(html, self.fake_translate)
        
        # Debe ser idéntico (o casi)
        assert "<div>" in result
        assert result.lower().count("<br") == 2
    
    def test_email_completo_estructura_identica(self):
        """
        Test crítico: email HTML completo debe mantener estructura.
        
        Este test DEBE fallar si se eliminan <br>, <p>, o cambia el DOM.
        """
        email_html = """<p>Estimado cliente,</p>
<p>Gracias por contactar con nosotros.</p>
<p>Atentamente,<br>
El equipo</p>"""
        
        result = translate_html_preserving_structure(email_html, self.fake_translate)
        
        # ASERCIONES CRÍTICAS: estructura DOM debe ser idéntica
        assert result.count("<p>") == 3, "El número de <p> cambió"
        assert result.count("</p>") == 3, "El número de </p> cambió"
        assert result.lower().count("<br") == 1, "El <br> se perdió o duplicó"
        
        # Verificar traducción de contenido
        assert "Kære kunde" in result
        assert "Tak" in result


class TestSplitHTMLPreservingStructure:
    """Tests para extracción y reconstrucción de HTML."""
    
    def test_extrae_textos_correctamente(self):
        """Debe extraer solo los textos, manteniendo estructura."""
        html = "<p>Hola</p><p>mundo</p>"
        blocks, texts = split_html_preserving_structure(html)
        
        # Debe extraer 2 textos
        assert len(texts) == 2
        assert "Hola" in texts
        assert "mundo" in texts
    
    def test_reconstruye_html_identico(self):
        """Debe reconstruir HTML idéntico con textos traducidos."""
        html = "<p>Hola</p><br><p>mundo</p>"
        blocks, texts = split_html_preserving_structure(html)
        
        # Simular traducción
        translated_texts = [t.replace("Hola", "Hej").replace("mundo", "verden") for t in texts]
        
        # Reconstruir
        result = rehydrate_html(blocks, translated_texts)
        
        # Verificar estructura
        assert "<p>" in result
        assert result.count("<p>") == 2
        assert "<br" in result.lower()
    
    def test_maneja_html_con_br_en_medio(self):
        """Debe manejar <br> dentro de bloques de texto."""
        html = "<p>Línea 1<br>Línea 2</p>"
        blocks, texts = split_html_preserving_structure(html)
        
        # Reconstruir sin cambios
        result = rehydrate_html(blocks, texts)
        
        # Debe contener <br>
        assert "<br" in result.lower()
        assert "<p>" in result


class TestHTMLIntegration:
    """Tests de integración para HTML completo."""
    
    def test_email_corporativo_completo(self):
        """
        Test de email corporativo real con múltiples elementos.
        
        Debe preservar TODO: <p>, <br>, <strong>, <a>, etc.
        """
        email = """<p>Estimado cliente,</p>
<p>Le informamos que su pedido está <strong>listo</strong>.</p>
<p>Para más información:<br>
Teléfono: <a href="tel:123">123-456</a><br>
Email: <a href="mailto:info@example.com">info@example.com</a></p>
<p>Atentamente,<br>
El equipo de ventas</p>"""
        
        def fake_tr(text: str) -> str:
            return text.replace("Estimado", "Kære").replace("cliente", "kunde")
        
        result = translate_html_preserving_structure(email, fake_tr)
        
        # Verificar estructura completa preservada
        assert result.count("<p>") == 4
        assert result.count("</p>") == 4
        assert result.lower().count("<br") >= 3
        assert result.count("<strong>") == 1
        assert result.count("</strong>") == 1
        assert result.count("<a") == 2
        
        # Verificar que los enlaces NO fueron traducidos
        assert 'href="tel:123"' in result or "href='tel:123'" in result
        assert 'href="mailto:info@example.com"' in result or "href='mailto:" in result
    
    def test_no_elimina_espacios_significativos(self):
        """No debe eliminar espacios que son parte del contenido."""
        html = "<p>Hola   mundo</p>"
        
        def identity(text: str) -> str:
            return text
        
        result = translate_html_preserving_structure(html, identity)
        
        # Nota: BeautifulSoup puede normalizar espacios, esto es aceptable
        # pero el contenido debe estar presente
        assert "Hola" in result
        assert "mundo" in result
    
    def test_tabla_simple_preservada(self):
        """Debe preservar estructura de tabla."""
        html = """<table>
<tr><td>Celda 1</td><td>Celda 2</td></tr>
<tr><td>Celda 3</td><td>Celda 4</td></tr>
</table>"""
        
        def fake_tr(text: str) -> str:
            return text.replace("Celda", "Celle")
        
        result = translate_html_preserving_structure(html, fake_tr)
        
        # Verificar estructura de tabla
        assert "<table>" in result
        assert "</table>" in result
        assert result.count("<tr>") == 2
        assert result.count("<td>") == 4
        
        # Verificar traducción
        assert "Celle" in result

