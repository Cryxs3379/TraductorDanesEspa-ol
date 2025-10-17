"""
Utilidades para procesamiento de HTML de correos electrónicos.

Extrae texto, traduce por bloques conservando estructura HTML básica,
y rehidrata el resultado manteniendo etiquetas y atributos importantes.

Etiquetas soportadas:
- Estructura: <p>, <div>, <br>, <hr>
- Listas: <ul>, <ol>, <li>
- Formato: <strong>, <b>, <em>, <i>, <u>, <span>
- Enlaces: <a> (preserva href)
- Encabezados: <h1>-<h6>
- Tabla: <table>, <tr>, <td>, <th> (básico)

Limitaciones:
- HTML complejo con JS/CSS inline puede perder formato
- Se recomienda usar en correos con HTML simple/limpio
"""
import re
import html
from typing import List, Dict, Tuple
from html.parser import HTMLParser


class EmailHTMLExtractor(HTMLParser):
    """
    Parser HTML que extrae texto preservando estructura básica.
    """
    
    # Etiquetas que generan salto de línea/separación
    BLOCK_TAGS = {'p', 'div', 'br', 'hr', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 
                  'li', 'tr', 'table', 'ul', 'ol'}
    
    # Etiquetas inline que preservamos
    INLINE_TAGS = {'strong', 'b', 'em', 'i', 'u', 'span', 'a'}
    
    def __init__(self):
        super().__init__()
        self.blocks = []
        self.current_block = []
        self.current_attrs = {}
        self.tag_stack = []
        
    def handle_starttag(self, tag, attrs):
        """Maneja apertura de etiquetas."""
        attrs_dict = dict(attrs)
        
        if tag in self.BLOCK_TAGS:
            # Guardar bloque actual si tiene contenido
            if self.current_block:
                text = ''.join(self.current_block).strip()
                if text:
                    self.blocks.append({
                        'type': 'text',
                        'content': text,
                        'tag': self.tag_stack[-1] if self.tag_stack else None
                    })
                self.current_block = []
            
            # Registrar tag especial
            if tag == 'br':
                self.blocks.append({'type': 'br'})
            elif tag == 'hr':
                self.blocks.append({'type': 'hr'})
            else:
                self.tag_stack.append(tag)
                
        elif tag in self.INLINE_TAGS:
            # Guardar tag inline con sus atributos
            if tag == 'a' and 'href' in attrs_dict:
                self.current_block.append(f"[[LINK_START::{attrs_dict['href']}]]")
            else:
                self.current_block.append(f"[[{tag.upper()}_START]]")
            self.tag_stack.append(tag)
    
    def handle_endtag(self, tag):
        """Maneja cierre de etiquetas."""
        if tag in self.BLOCK_TAGS and tag in ['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li']:
            # Guardar bloque al cerrar
            if self.current_block:
                text = ''.join(self.current_block).strip()
                if text:
                    self.blocks.append({
                        'type': 'text',
                        'content': text,
                        'tag': tag
                    })
                self.current_block = []
            
            if self.tag_stack and self.tag_stack[-1] == tag:
                self.tag_stack.pop()
                
        elif tag in self.INLINE_TAGS:
            # Marcar cierre de inline tag
            if tag == 'a':
                self.current_block.append("[[LINK_END]]")
            else:
                self.current_block.append(f"[[{tag.upper()}_END]]")
            
            if self.tag_stack and self.tag_stack[-1] == tag:
                self.tag_stack.pop()
    
    def handle_data(self, data):
        """Maneja texto."""
        if data.strip():
            self.current_block.append(data)
    
    def get_blocks(self) -> List[Dict]:
        """Retorna lista de bloques extraídos."""
        # Agregar bloque final si existe
        if self.current_block:
            text = ''.join(self.current_block).strip()
            if text:
                self.blocks.append({
                    'type': 'text',
                    'content': text,
                    'tag': self.tag_stack[-1] if self.tag_stack else None
                })
        return self.blocks


def extract_text_blocks(html_content: str) -> List[Dict]:
    """
    Extrae bloques de texto de HTML preservando estructura básica.
    
    Args:
        html_content: HTML del correo
        
    Returns:
        Lista de diccionarios con bloques:
        [
            {'type': 'text', 'content': 'texto', 'tag': 'p'},
            {'type': 'br'},
            ...
        ]
    """
    # Limpiar HTML: decodificar entidades
    html_content = html.unescape(html_content)
    
    # Parsear
    parser = EmailHTMLExtractor()
    try:
        parser.feed(html_content)
    except Exception as e:
        # Si el parsing falla, devolver texto plano
        text = re.sub(r'<[^>]+>', ' ', html_content)
        text = ' '.join(text.split())
        return [{'type': 'text', 'content': text, 'tag': 'p'}]
    
    return parser.get_blocks()


def translate_html_blocks(
    blocks: List[Dict],
    translate_fn,
    glossary: Dict[str, str] = None,
    max_new_tokens: int = 256
) -> List[Dict]:
    """
    Traduce bloques de texto extraídos de HTML.
    
    Args:
        blocks: Lista de bloques extraídos
        translate_fn: Función de traducción (debe aceptar list[str] y retornar list[str])
        glossary: Glosario opcional
        max_new_tokens: Max tokens por traducción
        
    Returns:
        Lista de bloques con contenido traducido
    """
    # Separar bloques de texto de los estructurales
    text_blocks = [b for b in blocks if b['type'] == 'text']
    
    if not text_blocks:
        return blocks
    
    # Extraer textos para traducir
    texts_to_translate = [b['content'] for b in text_blocks]
    
    # Traducir en batch
    translations = translate_fn(texts_to_translate)
    
    # Reemplazar contenido traducido
    translated_blocks = []
    text_idx = 0
    
    for block in blocks:
        if block['type'] == 'text':
            translated_blocks.append({
                'type': 'text',
                'content': translations[text_idx],
                'tag': block.get('tag')
            })
            text_idx += 1
        else:
            translated_blocks.append(block)
    
    return translated_blocks


def reconstruct_html(blocks: List[Dict]) -> str:
    """
    Reconstruye HTML a partir de bloques traducidos.
    
    Convierte marcadores inline de vuelta a etiquetas HTML.
    
    Args:
        blocks: Lista de bloques traducidos
        
    Returns:
        HTML reconstruido
    """
    html_parts = []
    
    for block in blocks:
        if block['type'] == 'br':
            html_parts.append('<br>')
        elif block['type'] == 'hr':
            html_parts.append('<hr>')
        elif block['type'] == 'text':
            content = block['content']
            tag = block.get('tag', 'p')
            
            # Convertir marcadores inline a HTML
            content = _restore_inline_tags(content)
            
            # Envolver en tag
            html_parts.append(f'<{tag}>{content}</{tag}>')
    
    return '\n'.join(html_parts)


def _restore_inline_tags(text: str) -> str:
    """
    Restaura etiquetas inline desde marcadores.
    
    Convierte:
    - [[STRONG_START]] -> <strong>
    - [[STRONG_END]] -> </strong>
    - [[LINK_START::url]] -> <a href="url">
    - [[LINK_END]] -> </a>
    etc.
    """
    # Enlaces
    text = re.sub(r'\[\[LINK_START::(.*?)\]\]', r'<a href="\1">', text)
    text = re.sub(r'\[\[LINK_END\]\]', '</a>', text)
    
    # Formato fuerte
    text = re.sub(r'\[\[STRONG_START\]\]', '<strong>', text)
    text = re.sub(r'\[\[STRONG_END\]\]', '</strong>', text)
    text = re.sub(r'\[\[B_START\]\]', '<b>', text)
    text = re.sub(r'\[\[B_END\]\]', '</b>', text)
    
    # Énfasis
    text = re.sub(r'\[\[EM_START\]\]', '<em>', text)
    text = re.sub(r'\[\[EM_END\]\]', '</em>', text)
    text = re.sub(r'\[\[I_START\]\]', '<i>', text)
    text = re.sub(r'\[\[I_END\]\]', '</i>', text)
    
    # Subrayado
    text = re.sub(r'\[\[U_START\]\]', '<u>', text)
    text = re.sub(r'\[\[U_END\]\]', '</u>', text)
    
    # Span
    text = re.sub(r'\[\[SPAN_START\]\]', '<span>', text)
    text = re.sub(r'\[\[SPAN_END\]\]', '</span>', text)
    
    return text


def translate_html(
    html_content: str,
    translate_fn,
    glossary: Dict[str, str] = None,
    max_new_tokens: int = 256
) -> str:
    """
    Traduce HTML de correo completo.
    
    Función de alto nivel que orquesta extracción, traducción y reconstrucción.
    
    Args:
        html_content: HTML original del correo
        translate_fn: Función de traducción que acepta list[str] y retorna list[str]
        glossary: Glosario opcional ES->DA
        max_new_tokens: Max tokens por traducción
        
    Returns:
        HTML traducido con estructura preservada
        
    Ejemplo:
        >>> html_in = '<p>Hola <strong>mundo</strong></p>'
        >>> html_out = translate_html(html_in, my_translate_function)
        >>> # '<p>Hej <strong>verden</strong></p>'
    """
    # 1. Extraer bloques
    blocks = extract_text_blocks(html_content)
    
    # 2. Traducir bloques
    translated_blocks = translate_html_blocks(
        blocks, 
        translate_fn, 
        glossary=glossary,
        max_new_tokens=max_new_tokens
    )
    
    # 3. Reconstruir HTML
    html_translated = reconstruct_html(translated_blocks)
    
    return html_translated


def sanitize_html(html_content: str) -> str:
    """
    Sanitiza HTML removiendo scripts, estilos inline peligrosos, etc.
    
    Propósito: prevenir XSS en la UI de previsualización.
    
    Args:
        html_content: HTML a sanitizar
        
    Returns:
        HTML limpio y seguro
    """
    # Remover scripts
    html_content = re.sub(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', '', html_content, flags=re.IGNORECASE)
    
    # Remover event handlers inline (onclick, onerror, etc.)
    html_content = re.sub(r'\s*on\w+\s*=\s*["\']?[^"\']*["\']?', '', html_content, flags=re.IGNORECASE)
    
    # Remover javascript: en hrefs
    html_content = re.sub(r'href\s*=\s*["\']?\s*javascript:', 'href="#', html_content, flags=re.IGNORECASE)
    
    # Remover estilos inline (opcional, puede romper formato)
    # html_content = re.sub(r'\s*style\s*=\s*["\']?[^"\']*["\']?', '', html_content, flags=re.IGNORECASE)
    
    return html_content

