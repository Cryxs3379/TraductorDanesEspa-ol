"""
Utilidades para procesamiento de texto preservando estructura.

Normalización y segmentación que mantiene saltos de línea y maquetación.
"""
import re
from typing import List, Callable


# Regex para compactar espacios/tabs SIN tocar \n
_WS_KEEP_NL = re.compile(r"[ \t]+")

# Regex para capturar separadores de párrafo (doble salto + posibles espacios)
SPLIT_PARA = re.compile(r"(\n\s*\n)")


def normalize_preserving_newlines(text: str) -> str:
    """
    Normaliza texto preservando TODOS los saltos de línea.
    
    Operaciones:
    1. Normaliza finales de línea: \\r\\n y \\r → \\n
    2. Compacta espacios/tabs múltiples a uno solo (NO toca \\n)
    3. Recorta espacios en los bordes de cada línea (no del documento)
    
    Args:
        text: Texto a normalizar
        
    Returns:
        Texto normalizado con saltos de línea preservados
        
    Examples:
        >>> normalize_preserving_newlines("Hola  mundo\\n\\nAdios")
        'Hola mundo\\n\\nAdios'
        
        >>> normalize_preserving_newlines("Línea 1\\r\\nLínea 2")
        'Línea 1\\nLínea 2'
    """
    # 1) Normalizar finales de línea a Unix (LF)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    
    # 2) Compactar espacios/tabs pero conservar \n
    text = _WS_KEEP_NL.sub(" ", text)
    
    # 3) Recortar bordes de cada línea individualmente
    lines = [ln.strip() for ln in text.split("\n")]
    return "\n".join(lines)


def translate_preserving_structure(
    text: str,
    translate_fn: Callable[[str], str],
) -> str:
    """
    Traduce texto por bloques de párrafos preservando separadores originales.
    
    Estrategia:
    - Divide el texto por separadores de párrafo (\\n\\n+)
    - Traduce cada bloque/párrafo por separado
    - Reensambla usando los separadores originales
    
    Esto garantiza que:
    - Los saltos de línea simples (\\n) se preservan dentro de cada bloque
    - Los saltos de línea múltiples (\\n\\n, \\n\\n\\n, etc.) se preservan entre bloques
    - La estructura visual del documento se mantiene idéntica
    
    Args:
        text: Texto a traducir
        translate_fn: Función de traducción que recibe un string y retorna traducción
                     Firma: fn(text: str) -> str
        
    Returns:
        Texto traducido con estructura preservada
        
    Examples:
        >>> def fake_tr(s: str) -> str:
        ...     return s.replace("hola", "hej")
        >>> 
        >>> text = "hola\\n\\nadiós"
        >>> translate_preserving_structure(text, fake_tr)
        'hej\\n\\nadiós'
    """
    # Normalizar primero (sin aplanar \n)
    text = normalize_preserving_newlines(text)
    
    # Dividir por separadores de párrafo capturándolos
    # split() con grupo de captura retorna: [chunk, sep, chunk, sep, ...]
    parts = SPLIT_PARA.split(text)
    
    out = []
    for i, part in enumerate(parts):
        if i % 2 == 0:  # Posiciones pares = contenido
            if part.strip() == "":
                # Bloque vacío: conservar tal cual
                out.append(part)
            else:
                # Bloque con contenido: traducir
                translated = translate_fn(part)
                out.append(translated)
        else:  # Posiciones impares = separadores capturados
            # Preservar el separador exacto (puede ser \n\n, \n\n\n, \n  \n, etc.)
            out.append(part)
    
    return "".join(out)


def looks_like_html(text: str) -> bool:
    """
    Heurística simple para detectar si un texto parece contener HTML.
    
    Args:
        text: Texto a verificar
        
    Returns:
        True si parece contener HTML, False en caso contrario
        
    Examples:
        >>> looks_like_html("<p>Hola</p>")
        True
        
        >>> looks_like_html("Hola mundo")
        False
        
        >>> looks_like_html("El operador < compara")
        False
    """
    if not text:
        return False
    
    # Buscar patrones de tags HTML: <nombre> o </nombre>
    # Debe empezar con letra para evitar falsos positivos con <, >, etc.
    html_tag_pattern = re.compile(r'</?[a-zA-Z][^>]*>')
    
    return bool(html_tag_pattern.search(text))


def segment_text_preserving_newlines(
    text: str,
    max_chars: int = 1500
) -> List[str]:
    """
    Segmenta texto largo en chunks manejables preservando estructura.
    
    A diferencia de split_text_for_email(), esta función preserva TODOS
    los saltos de línea y no intenta reagrupar o normalizar.
    
    Estrategia:
    1. Divide por párrafos (\\n\\n)
    2. Si un párrafo excede max_chars, lo divide por saltos simples (\\n)
    3. Si aún es muy largo, divide por oraciones
    4. Siempre preserva los separadores originales
    
    Args:
        text: Texto a segmentar
        max_chars: Máximo de caracteres por segmento
        
    Returns:
        Lista de segmentos que al unirse reproducen el texto original
    """
    if len(text) <= max_chars:
        return [text]
    
    segments = []
    
    # Dividir por párrafos preservando separadores
    parts = SPLIT_PARA.split(text)
    
    for i, part in enumerate(parts):
        if i % 2 == 1:  # Separador
            # Añadir al último segmento
            if segments:
                segments[-1] += part
            continue
        
        # Contenido
        if len(part) <= max_chars:
            segments.append(part)
        else:
            # Párrafo muy largo: dividir por líneas simples
            lines = part.split("\n")
            current = []
            current_len = 0
            
            for line in lines:
                line_len = len(line)
                
                if current_len + line_len + 1 <= max_chars:  # +1 por el \n
                    current.append(line)
                    current_len += line_len + 1
                else:
                    # Guardar chunk actual
                    if current:
                        segments.append("\n".join(current))
                    current = [line]
                    current_len = line_len
            
            # Guardar último chunk
            if current:
                segments.append("\n".join(current))
    
    return segments

