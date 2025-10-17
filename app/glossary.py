"""
Utilidades para manejo de glosario terminológico.

Implementa una estrategia conservadora para preservar términos específicos:
- Pre-procesamiento: envuelve términos ES con marcadores [[TERM::<texto>]]
- Post-procesamiento: reemplaza marcadores por términos DA correspondientes

Limitaciones:
- Los marcadores pueden alterar la puntuación adyacente
- Términos multi-palabra pueden causar problemas con tokenización
- Se recomienda usar términos completos y no fragmentos
"""
import re
from typing import Dict


def apply_glossary_pre(text: str, glossary: Dict[str, str]) -> str:
    """
    Aplica glosario en pre-procesamiento: marca términos ES para protegerlos.
    
    Args:
        text: Texto en español original
        glossary: Diccionario {término_es: término_da}
        
    Returns:
        Texto con términos marcados como [[TERM::<término_es>]]
        
    Estrategia:
        - Ordena términos por longitud descendente (evitar matches parciales)
        - Búsqueda case-insensitive pero preserva case original
        - Usa word boundaries para evitar matches parciales
    """
    if not glossary:
        return text
    
    result = text
    
    # Ordenar términos por longitud (más largos primero) para evitar matches parciales
    sorted_terms = sorted(glossary.keys(), key=len, reverse=True)
    
    for term_es in sorted_terms:
        # Escapar caracteres especiales de regex
        escaped_term = re.escape(term_es)
        
        # Pattern con word boundaries para match exacto (case-insensitive)
        # Captura el término con su case original
        pattern = r'\b(' + escaped_term + r')\b'
        
        # Reemplazar con marcador, preservando el case original
        result = re.sub(
            pattern,
            r'[[TERM::\1]]',
            result,
            flags=re.IGNORECASE
        )
    
    return result


def apply_glossary_post(text: str, glossary: Dict[str, str]) -> str:
    """
    Aplica glosario en post-procesamiento: reemplaza marcadores por términos DA.
    
    Args:
        text: Texto traducido con marcadores [[TERM::...]]
        glossary: Diccionario {término_es: término_da}
        
    Returns:
        Texto con marcadores reemplazados por términos daneses
        
    Nota:
        - Busca todos los marcadores [[TERM::<algo>]]
        - Busca <algo> en el glosario (case-insensitive)
        - Reemplaza con el término danés correspondiente
    """
    if not glossary:
        return text
    
    result = text
    
    # Crear diccionario case-insensitive para lookup
    glossary_lower = {k.lower(): v for k, v in glossary.items()}
    
    # Pattern para encontrar todos los marcadores
    pattern = r'\[\[TERM::(.*?)\]\]'
    
    def replace_marker(match):
        """Función de reemplazo para cada marcador encontrado."""
        original_term = match.group(1)
        term_lower = original_term.lower()
        
        # Buscar término en glosario (case-insensitive)
        if term_lower in glossary_lower:
            return glossary_lower[term_lower]
        
        # Si no se encuentra, devolver sin marcador (fallback)
        return original_term
    
    result = re.sub(pattern, replace_marker, result)
    
    return result


def clean_glossary_markers(text: str) -> str:
    """
    Limpia cualquier marcador residual que no se haya procesado.
    
    Args:
        text: Texto que puede contener marcadores [[TERM::...]]
        
    Returns:
        Texto sin marcadores
        
    Uso:
        Función de seguridad para casos donde el post-procesamiento falla.
    """
    pattern = r'\[\[TERM::(.*?)\]\]'
    return re.sub(pattern, r'\1', text)

