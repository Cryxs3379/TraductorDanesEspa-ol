"""
Segmentación de texto plano para traducciones largas.

Reutiliza la lógica existente de segment.py para texto plano.
"""
from typing import List
from app.segment import split_text_for_email


def split_text_for_plain(text: str, max_segment_chars: int = 800) -> List[str]:
    """
    Segmenta texto plano largo en fragmentos manejables.
    
    Reutiliza split_text_for_email (ya testeado) que segmenta por
    párrafos y puntos, preservando delimitadores.
    
    Args:
        text: Texto a segmentar
        max_segment_chars: Máximo de caracteres por segmento (default: 800)
        
    Returns:
        Lista de segmentos de texto
        
    Examples:
        >>> text = "Primera frase. Segunda frase. " * 100  # ~2800 chars
        >>> segments = split_text_for_plain(text, max_segment_chars=800)
        >>> len(segments) > 1
        True
        >>> all(len(s) <= 1000 for s in segments)  # margen de tolerancia
        True
    """
    return split_text_for_email(text, max_segment_chars=max_segment_chars)

