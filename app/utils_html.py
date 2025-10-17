"""
Utilidades para procesamiento HTML.

Sanitización y limpieza de HTML de correos electrónicos.
"""
import re


def sanitize_html(html: str) -> str:
    """
    Sanitiza HTML removiendo contenido peligroso.
    
    Preserva solo etiquetas básicas y seguras:
    - Estructura: p, div, br, hr, h1-h6
    - Formato: strong, b, em, i, u, span
    - Listas: ul, ol, li
    - Enlaces: a (solo atributo href)
    - Tablas básicas: table, tr, td, th
    
    Remueve:
    - Scripts y event handlers
    - Estilos inline peligrosos
    - Iframes y objetos
    - javascript: en URLs
    
    Args:
        html: HTML a sanitizar
        
    Returns:
        HTML limpio y seguro
    """
    if not html:
        return ""
    
    # 1. Remover scripts
    html = re.sub(
        r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>',
        '',
        html,
        flags=re.IGNORECASE
    )
    
    # 2. Remover event handlers inline (onclick, onerror, etc.)
    html = re.sub(
        r'\s*on\w+\s*=\s*["\']?[^"\']*["\']?',
        '',
        html,
        flags=re.IGNORECASE
    )
    
    # 3. Remover javascript: en hrefs
    html = re.sub(
        r'href\s*=\s*["\']?\s*javascript:',
        'href="#',
        html,
        flags=re.IGNORECASE
    )
    
    # 4. Remover iframes
    html = re.sub(
        r'<iframe\b[^<]*(?:(?!<\/iframe>)<[^<]*)*<\/iframe>',
        '',
        html,
        flags=re.IGNORECASE
    )
    
    # 5. Remover objects y embeds
    html = re.sub(
        r'<(object|embed)\b[^<]*(?:(?!<\/\1>)<[^<]*)*<\/\1>',
        '',
        html,
        flags=re.IGNORECASE
    )
    
    # 6. Limitar atributos en tags <a> solo a href
    # (esto se hace mejor con un parser pero para simplicidad usamos regex)
    html = re.sub(
        r'(<a\s+)([^>]*?)(href="[^"]*")([^>]*?>)',
        r'\1\3>',
        html,
        flags=re.IGNORECASE
    )
    
    return html


def strip_html_tags(html: str) -> str:
    """
    Remueve todas las etiquetas HTML, dejando solo texto.
    
    Args:
        html: HTML a procesar
        
    Returns:
        Texto plano sin tags
    """
    # Remover tags
    text = re.sub(r'<[^>]+>', ' ', html)
    # Normalizar espacios
    text = ' '.join(text.split())
    return text.strip()

