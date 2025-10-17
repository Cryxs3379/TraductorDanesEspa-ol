"""
Segmentación de texto y HTML para traducción de correos electrónicos.

Divide textos largos en segmentos manejables preservando contexto y estructura.
"""
import re
from typing import List, Dict
from html.parser import HTMLParser


def split_text_for_email(text: str, max_segment_chars: int = 600) -> List[str]:
    """
    Segmenta texto por frases/párrafos preservando delimitadores.
    
    Estrategia:
    - Divide por párrafos (\n\n) primero
    - Si un párrafo es muy largo, divide por oraciones (. ! ?)
    - Preserva puntuación
    
    Args:
        text: Texto a segmentar
        max_segment_chars: Longitud máxima recomendada por segmento
        
    Returns:
        Lista de segmentos de texto
    """
    if not text or len(text) <= max_segment_chars:
        return [text] if text else []
    
    segments = []
    
    # 1. Dividir por párrafos dobles
    paragraphs = text.split('\n\n')
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        # Si el párrafo es corto, añadirlo directamente
        if len(para) <= max_segment_chars:
            segments.append(para)
            continue
        
        # 2. Dividir párrafo largo por oraciones
        # Buscar puntos finales seguidos de espacio y mayúscula
        sentence_pattern = r'([.!?]+\s+)(?=[A-ZÁÉÍÓÚÑ¿¡])'
        sentences = re.split(sentence_pattern, para)
        
        # Reconstruir oraciones con su puntuación
        current_segment = ""
        i = 0
        while i < len(sentences):
            sentence = sentences[i]
            
            # Si es un delimitador, agregarlo al anterior
            if re.match(r'^[.!?]+\s+$', sentence):
                if current_segment:
                    current_segment += sentence
                i += 1
                continue
            
            # Si agregar esta oración excede el límite, guardar segmento actual
            if current_segment and len(current_segment + sentence) > max_segment_chars:
                segments.append(current_segment.strip())
                current_segment = sentence
            else:
                current_segment += sentence
            
            i += 1
        
        # Agregar último segmento
        if current_segment:
            segments.append(current_segment.strip())
    
    return segments


class HTMLBlockExtractor(HTMLParser):
    """
    Extrae bloques de HTML preservando estructura para rehidratación.
    
    Genera lista de bloques:
    - {"type": "text", "content": "...", "tag": "p"}
    - {"type": "tag_open", "name": "strong", "attrs": {}}
    - {"type": "tag_close", "name": "strong"}
    - {"type": "tag_self", "name": "br"}
    """
    
    # Tags que contienen texto traducible
    TEXT_CONTAINERS = {'p', 'div', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'td', 'th', 'span'}
    
    # Tags inline que se preservan
    INLINE_TAGS = {'strong', 'b', 'em', 'i', 'u', 'a', 'span'}
    
    # Tags self-closing
    SELF_CLOSING = {'br', 'hr', 'img'}
    
    def __init__(self):
        super().__init__()
        self.blocks = []
        self.current_text = []
        self.text_index = 0  # Índice para mapear traducciones
        
    def handle_starttag(self, tag, attrs):
        """Maneja apertura de etiquetas."""
        attrs_dict = dict(attrs) if attrs else {}
        
        if tag in self.SELF_CLOSING:
            # Guardar texto actual si existe
            self._flush_text()
            self.blocks.append({
                'type': 'tag_self',
                'name': tag,
                'attrs': attrs_dict
            })
        elif tag in self.TEXT_CONTAINERS or tag in self.INLINE_TAGS:
            # Guardar contexto de tag
            self.blocks.append({
                'type': 'tag_open',
                'name': tag,
                'attrs': attrs_dict
            })
    
    def handle_endtag(self, tag):
        """Maneja cierre de etiquetas."""
        if tag in self.TEXT_CONTAINERS:
            # Flush texto antes de cerrar contenedor
            self._flush_text()
        
        if tag in self.TEXT_CONTAINERS or tag in self.INLINE_TAGS:
            self.blocks.append({
                'type': 'tag_close',
                'name': tag
            })
    
    def handle_data(self, data):
        """Maneja texto."""
        if data.strip():
            self.current_text.append(data)
    
    def _flush_text(self):
        """Guarda el texto acumulado como bloque."""
        if self.current_text:
            text = ''.join(self.current_text).strip()
            if text:
                self.blocks.append({
                    'type': 'text',
                    'content': text,
                    'index': self.text_index
                })
                self.text_index += 1
            self.current_text = []
    
    def get_blocks(self) -> List[Dict]:
        """Retorna bloques extraídos."""
        self._flush_text()
        return self.blocks


def split_html_preserving_structure(html: str) -> tuple[List[Dict], List[str]]:
    """
    Extrae bloques de HTML y textos para traducir.
    
    Args:
        html: HTML del correo
        
    Returns:
        Tupla (bloques_estructura, textos_a_traducir)
        - bloques_estructura: lista de bloques para reconstrucción
        - textos_a_traducir: lista de textos extraídos (en orden)
    """
    parser = HTMLBlockExtractor()
    
    try:
        parser.feed(html)
    except Exception:
        # Si el parsing falla, tratar como texto plano
        return (
            [{'type': 'text', 'content': html, 'index': 0}],
            [html]
        )
    
    blocks = parser.get_blocks()
    
    # Extraer textos en orden
    texts = []
    for block in blocks:
        if block['type'] == 'text':
            texts.append(block['content'])
    
    return blocks, texts


def rehydrate_html(blocks: List[Dict], translations: List[str]) -> str:
    """
    Reconstruye HTML insertando traducciones.
    
    Args:
        blocks: Bloques de estructura original
        translations: Traducciones correspondientes a bloques de texto (mismo orden)
        
    Returns:
        HTML reconstruido con textos traducidos
    """
    html_parts = []
    
    for block in blocks:
        if block['type'] == 'text':
            # Insertar traducción correspondiente
            idx = block.get('index', 0)
            if idx < len(translations):
                html_parts.append(translations[idx])
            else:
                # Fallback: usar contenido original
                html_parts.append(block['content'])
                
        elif block['type'] == 'tag_open':
            # Reconstruir tag de apertura con atributos
            tag = block['name']
            attrs = block.get('attrs', {})
            
            if attrs:
                attrs_str = ' '.join(f'{k}="{v}"' for k, v in attrs.items())
                html_parts.append(f'<{tag} {attrs_str}>')
            else:
                html_parts.append(f'<{tag}>')
                
        elif block['type'] == 'tag_close':
            html_parts.append(f'</{block["name"]}>')
            
        elif block['type'] == 'tag_self':
            tag = block['name']
            attrs = block.get('attrs', {})
            
            if attrs:
                attrs_str = ' '.join(f'{k}="{v}"' for k, v in attrs.items())
                html_parts.append(f'<{tag} {attrs_str}>')
            else:
                html_parts.append(f'<{tag}>')
    
    return ''.join(html_parts)

