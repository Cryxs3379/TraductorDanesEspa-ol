"""
Utilidades centralizadas para sanitización y procesamiento HTML seguro.

Garantiza que todo HTML procesado sea sanitizado consistentemente.
"""
import re
from typing import List, Dict, Any
from bs4 import BeautifulSoup, NavigableString, Tag


def sanitize_html(html_content: str) -> str:
    """
    Sanitiza HTML eliminando contenido peligroso.
    
    Args:
        html_content: HTML de entrada
        
    Returns:
        HTML sanitizado y seguro
    """
    if not html_content or not html_content.strip():
        return ""
    
    # Parsear HTML con BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Etiquetas permitidas para emails/correos
    allowed_tags = {
        'p', 'br', 'strong', 'em', 'b', 'i', 'u', 'span', 'div',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'ul', 'ol', 'li', 'blockquote',
        'a', 'img', 'table', 'tr', 'td', 'th', 'thead', 'tbody'
    }
    
    # Atributos permitidos
    allowed_attrs = {
        'href', 'src', 'alt', 'title', 'class', 'id', 'style',
        'width', 'height', 'align', 'valign', 'colspan', 'rowspan'
    }
    
    # Limpiar etiquetas no permitidas pero mantener su contenido
    for tag in soup.find_all():
        if tag.name not in allowed_tags:
            tag.unwrap()
        else:
            # Limpiar atributos no permitidos
            if hasattr(tag, 'attrs'):
                attrs_to_remove = []
                for attr in tag.attrs:
                    if attr.lower() not in allowed_attrs:
                        attrs_to_remove.append(attr)
                for attr in attrs_to_remove:
                    del tag.attrs[attr]
            
            # Sanitizar URLs en href/src para evitar javascript:, data:, etc.
            if tag.name == 'a' and 'href' in tag.attrs:
                href = tag.attrs['href']
                if not _is_safe_url(href):
                    # Convertir a texto si la URL no es segura
                    tag.name = 'span'
                    del tag.attrs['href']
            
            if tag.name == 'img' and 'src' in tag.attrs:
                src = tag.attrs['src']
                if not _is_safe_url(src):
                    # Eliminar imagen si src no es segura
                    tag.decompose()
    
    # Limpiar scripts, styles y otros elementos peligrosos que puedan haber quedado
    for element in soup.find_all(['script', 'style', 'iframe', 'object', 'embed']):
        element.decompose()
    
    return str(soup)


def _is_safe_url(url: str) -> bool:
    """
    Verifica si una URL es segura para mostrar.
    
    Args:
        url: URL a verificar
        
    Returns:
        True si la URL es segura, False en caso contrario
    """
    if not url:
        return False
    
    url_lower = url.lower().strip()
    
    # Protocolos peligrosos
    dangerous_protocols = [
        'javascript:', 'data:', 'vbscript:', 'file:', 
        'about:', 'chrome:', 'chrome-extension:'
    ]
    
    for protocol in dangerous_protocols:
        if url_lower.startswith(protocol):
            return False
    
    # URLs relativas y absolutas seguras están bien
    return url_lower.startswith(('http://', 'https://', 'mailto:', '/')) or not ':' in url_lower


def extract_text_for_translation(html_content: str) -> List[Dict[str, Any]]:
    """
    Extrae texto de HTML preservando estructura para traducción.
    
    Args:
        html_content: HTML de entrada sanitizado
        
    Returns:
        Lista de bloques con texto y metadatos de estructura
    """
    if not html_content or not html_content.strip():
        return []
    
    # Sanitizar primero
    sanitized_html = sanitize_html(html_content)
    soup = BeautifulSoup(sanitized_html, 'html.parser')
    
    blocks = []
    
    def extract_from_element(element, block_id: int = 0):
        if isinstance(element, NavigableString):
            text = str(element).strip()
            if text:
                blocks.append({
                    'id': block_id,
                    'text': text,
                    'type': 'text',
                    'element': None
                })
                return block_id + 1
        
        elif isinstance(element, Tag):
            # Extraer texto directo del elemento
            direct_text = ''
            for child in element.children:
                if isinstance(child, NavigableString):
                    direct_text += str(child).strip() + ' '
            
            if direct_text.strip():
                blocks.append({
                    'id': block_id,
                    'text': direct_text.strip(),
                    'type': 'text',
                    'element': {
                        'tag': element.name,
                        'attrs': dict(element.attrs)
                    }
                })
                block_id += 1
            
            # Procesar elementos hijos
            for child in element.children:
                if isinstance(child, Tag):
                    block_id = extract_from_element(child, block_id)
        
        return block_id
    
    # Procesar elementos principales
    for element in soup.find_all(['p', 'div', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'td', 'th']):
        extract_from_element(element)
    
    return blocks


def rebuild_html(blocks: List[Dict[str, Any]], translations: List[str]) -> str:
    """
    Reconstruye HTML usando bloques y traducciones.
    
    Args:
        blocks: Bloques de texto extraídos
        translations: Traducciones correspondientes
        
    Returns:
        HTML reconstruido
    """
    if len(blocks) != len(translations):
        raise ValueError("Número de bloques y traducciones no coincide")
    
    # Construir HTML preservando estructura
    html_parts = []
    
    for block, translation in zip(blocks, translations):
        if block['type'] == 'text':
            if block['element'] and block['element']['tag']:
                # Reconstruir con etiquetas
                tag = block['element']['tag']
                attrs_str = ''
                
                if block['element']['attrs']:
                    attrs_parts = []
                    for attr, value in block['element']['attrs'].items():
                        # Escapar atributos para seguridad
                        escaped_value = re.sub(r'[<>"\'\s]', '', str(value))
                        attrs_parts.append(f'{attr}="{escaped_value}"')
                    attrs_str = ' ' + ' '.join(attrs_parts)
                
                html_parts.append(f'<{tag}{attrs_str}>{translation}</{tag}>')
            else:
                html_parts.append(translation)
    
    return '\n'.join(html_parts)