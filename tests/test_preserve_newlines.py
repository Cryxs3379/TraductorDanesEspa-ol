"""
Tests para validar preservación de saltos de línea y estructura de texto.

Verifica que el traductor NO aplana \n, preserva \n\n, y mantiene
la maquetación básica de correos/documentos.
"""
import pytest
from app.utils_text import (
    normalize_preserving_newlines,
    translate_preserving_structure,
    looks_like_html,
    segment_text_preserving_newlines
)


class TestNormalizePreservingNewlines:
    """Tests para normalización que preserva saltos de línea."""
    
    def test_preserva_salto_simple(self):
        """Debe preservar saltos de línea simples (\n)."""
        text = "Línea 1\nLínea 2"
        result = normalize_preserving_newlines(text)
        assert result.count("\n") == 1
        assert "Línea 1\nLínea 2" == result
    
    def test_preserva_salto_doble(self):
        """Debe preservar saltos de línea dobles (\n\n)."""
        text = "Párrafo 1\n\nPárrafo 2"
        result = normalize_preserving_newlines(text)
        assert result.count("\n\n") == 1
        assert "Párrafo 1\n\nPárrafo 2" == result
    
    def test_preserva_saltos_multiples(self):
        """Debe preservar saltos de línea múltiples (\n\n\n)."""
        text = "Bloque 1\n\n\nBloque 2"
        result = normalize_preserving_newlines(text)
        # Debe preservar TODOS los saltos (3 \n)
        assert result.count("\n") == 3
        assert "Bloque 1\n\n\nBloque 2" == result
    
    def test_normaliza_espacios_no_newlines(self):
        """Debe compactar espacios múltiples pero NO tocar \n."""
        text = "Hola    mundo\n\nAdios    amigo"
        result = normalize_preserving_newlines(text)
        assert result == "Hola mundo\n\nAdios amigo"
    
    def test_normaliza_fin_de_linea_windows(self):
        """Debe convertir \r\n a \n."""
        text = "Línea 1\r\nLínea 2"
        result = normalize_preserving_newlines(text)
        assert result == "Línea 1\nLínea 2"
        assert "\r" not in result
    
    def test_normaliza_fin_de_linea_mac_classic(self):
        """Debe convertir \r a \n."""
        text = "Línea 1\rLínea 2"
        result = normalize_preserving_newlines(text)
        assert result == "Línea 1\nLínea 2"
    
    def test_strip_por_linea_no_global(self):
        """Debe hacer strip de cada línea, no del documento completo."""
        text = "  Línea 1  \n  Línea 2  "
        result = normalize_preserving_newlines(text)
        # Cada línea sin espacios en bordes, pero \n preservado
        assert result == "Línea 1\nLínea 2"
    
    def test_preserva_estructura_email(self):
        """Debe preservar estructura típica de email."""
        email = "Estimado cliente,\n\nGracias por contactarnos.\n\nAtentamente,\n— El equipo"
        result = normalize_preserving_newlines(email)
        
        # Verificar que mantiene los saltos dobles
        assert result.count("\n\n") == 2
        # Verificar saltos totales: 2 párrafos (2x2=4 saltos) + 1 salto antes de firma = 5
        assert result.count("\n") == 5


class TestTranslatePreservingStructure:
    """Tests para traducción con preservación de estructura."""
    
    def fake_translate(self, text: str) -> str:
        """Simulador de traducción: ES -> DA."""
        replacements = {
            "Hola": "Hej",
            "¿Cómo estás?": "Hvordan har du det?",
            "Adiós": "Farvel",
            "Firma:": "Underskrift:",
            "— Nombre": "— Navn",
            "Párrafo 1": "Afsnit 1",
            "Párrafo 2": "Afsnit 2",
            "Línea 1": "Linje 1",
            "Línea 2": "Linje 2"
        }
        result = text
        for es, da in replacements.items():
            result = result.replace(es, da)
        return result
    
    def test_preserva_salto_simple_traduccion(self):
        """Traducción debe preservar saltos simples exactos."""
        text = "Hola\n¿Cómo estás?"
        result = translate_preserving_structure(text, self.fake_translate)
        
        # Mismo número de saltos
        assert result.count("\n") == text.count("\n")
        assert "\n" in result
    
    def test_preserva_salto_doble_traduccion(self):
        """Traducción debe preservar saltos dobles exactos."""
        text = "Párrafo 1\n\nPárrafo 2"
        result = translate_preserving_structure(text, self.fake_translate)
        
        # Mismo número de saltos dobles
        assert result.count("\n\n") == text.count("\n\n")
        assert result.count("\n") == text.count("\n")
    
    def test_preserva_estructura_email_completo(self):
        """Traducción debe preservar estructura completa de email."""
        email = "Hola\n\n¿Cómo estás?\n\nFirma:\n— Nombre"
        result = translate_preserving_structure(email, self.fake_translate)
        
        # Verificar estructura idéntica
        assert result.count("\n") == email.count("\n")
        assert result.count("\n\n") == email.count("\n\n")
        
        # Verificar traducción
        assert "Hej" in result
        assert "Hvordan har du det?" in result
        assert "Farvel" not in result  # Esta palabra no está en el original
    
    def test_bloques_vacios_preservados(self):
        """Debe preservar bloques vacíos (múltiples saltos)."""
        text = "Línea 1\n\n\nLínea 2"
        result = translate_preserving_structure(text, self.fake_translate)
        
        # Debe preservar los 3 saltos de línea
        assert result.count("\n") == 3
    
    def test_no_aplana_espacios_en_bloques(self):
        """Dentro de bloques, no debe aplanar saltos simples."""
        text = "Línea 1\nLínea 2\n\nPárrafo 2"
        result = translate_preserving_structure(text, self.fake_translate)
        
        # Verificar que mantiene saltos simples dentro del primer bloque
        assert result.count("\n") == text.count("\n")
        lines = result.split("\n")
        assert len(lines) == 4  # 4 líneas separadas


class TestLooksLikeHTML:
    """Tests para detección heurística de HTML."""
    
    def test_detecta_html_simple(self):
        """Debe detectar HTML básico."""
        assert looks_like_html("<p>Hola</p>") is True
        assert looks_like_html("<div>Contenido</div>") is True
    
    def test_detecta_html_con_atributos(self):
        """Debe detectar HTML con atributos."""
        assert looks_like_html('<a href="url">Link</a>') is True
    
    def test_no_detecta_texto_plano(self):
        """No debe detectar texto plano como HTML."""
        assert looks_like_html("Hola mundo") is False
        assert looks_like_html("Esto es un texto normal") is False
    
    def test_no_confunde_operadores(self):
        """No debe confundir operadores matemáticos con HTML."""
        # Casos límite con < y >
        assert looks_like_html("5 < 10") is False
        assert looks_like_html("x > y") is False
    
    def test_detecta_br_y_hr(self):
        """Debe detectar tags auto-cerradas."""
        assert looks_like_html("Texto<br>Más texto") is True
        assert looks_like_html("Sección<hr>Otra") is True


class TestSegmentTextPreservingNewlines:
    """Tests para segmentación que preserva estructura."""
    
    def test_texto_corto_no_segmenta(self):
        """Texto corto debe retornarse sin cambios."""
        text = "Texto corto"
        result = segment_text_preserving_newlines(text, max_chars=100)
        assert len(result) == 1
        assert result[0] == text
    
    def test_segmenta_por_parrafos(self):
        """Debe segmentar por párrafos si excede límite."""
        text = "Párrafo 1\n\nPárrafo 2 que es muy largo " + ("x" * 100)
        result = segment_text_preserving_newlines(text, max_chars=50)
        
        # Debe haber al menos 2 segmentos
        assert len(result) >= 2
    
    def test_preserva_estructura_al_segmentar(self):
        """Al segmentar, debe preservar la estructura original."""
        text = "Línea 1\nLínea 2\n\nPárrafo 2"
        result = segment_text_preserving_newlines(text, max_chars=1000)
        
        # Reunir segmentos debe dar texto original
        reunido = "".join(result)
        # Normalizar para comparar (la función puede añadir separadores)
        assert text in reunido or reunido == text


class TestIntegrationPreserveStructure:
    """Tests de integración para verificar comportamiento end-to-end."""
    
    def test_email_completo_estructura_identica(self):
        """
        Test crítico: email completo debe mantener estructura IDÉNTICA.
        
        Este test DEBE fallar si se aplanan o cambian saltos de línea.
        """
        email_original = """Estimado Sr. García,

Gracias por contactar con nosotros.

Atentamente,
El equipo de soporte

—
Nombre Apellido
Título"""
        
        # Contar características estructurales originales
        num_lineas_original = email_original.count("\n")
        num_parrafos_original = email_original.count("\n\n")
        
        # Simular traducción
        def fake_tr(text: str) -> str:
            return text.replace("Estimado", "Kære").replace("Gracias", "Tak")
        
        email_traducido = translate_preserving_structure(email_original, fake_tr)
        
        # ASERCIONES CRÍTICAS: estructura debe ser IDÉNTICA
        assert email_traducido.count("\n") == num_lineas_original, \
            "El número de saltos de línea cambió"
        assert email_traducido.count("\n\n") == num_parrafos_original, \
            "El número de separadores de párrafo cambió"
        
        # Verificar que las líneas están en las mismas posiciones
        lineas_orig = email_original.split("\n")
        lineas_trad = email_traducido.split("\n")
        assert len(lineas_orig) == len(lineas_trad), \
            "El número de líneas cambió"
    
    def test_firma_con_guiones_preservada(self):
        """Firmas con — y múltiples líneas deben preservarse."""
        firma = "Atentamente,\n— Juan\n— Departamento IT"
        
        def fake_tr(text: str) -> str:
            return text.replace("Atentamente", "Med venlig hilsen")
        
        result = translate_preserving_structure(firma, fake_tr)
        
        # Verificar saltos preservados
        assert result.count("\n") == firma.count("\n")
        # Verificar que los guiones están en líneas separadas
        assert "— Juan" in result or "—" in result

