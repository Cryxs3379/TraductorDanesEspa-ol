"""
Utilidades para manejo de glosario terminológico.

Implementa una estrategia conservadora para preservar términos específicos:
- Pre-procesamiento: envuelve términos ES con marcadores [[TERM::<texto>]]
- Post-procesamiento: reemplaza marcadores por términos DA correspondientes

Protege automáticamente:
- URLs (http://, https://, www.)
- Emails (usuario@dominio.com)
- Números (enteros, decimales, con separadores)
- Términos del glosario personalizado

Limitaciones:
- Los marcadores pueden alterar la puntuación adyacente en casos complejos
- Se recomienda usar términos completos y no fragmentos
"""
import re
from typing import Dict, List, Tuple


def _protect_entities(text: str) -> Tuple[str, List[Tuple[str, str]]]:
    """
    Protege entidades especiales (URLs, emails, números) reemplazándolas con placeholders.
    
    Returns:
        Tupla (texto_con_placeholders, lista_de_entidades_protegidas)
    """
    protected = []
    result = text
    
    # 1. Proteger URLs (http://, https://, www.)
    url_pattern = r'(https?://[^\s]+|www\.[^\s]+)'
    urls = re.findall(url_pattern, result)
    for i, url in enumerate(urls):
        placeholder = f"__URL_{i}__"
        protected.append((placeholder, url))
        result = result.replace(url, placeholder, 1)
    
    # 2. Proteger emails
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, result)
    for i, email in enumerate(emails):
        placeholder = f"__EMAIL_{i}__"
        protected.append((placeholder, email))
        result = result.replace(email, placeholder, 1)
    
    # 3. Proteger números (enteros, decimales, con separadores)
    # Incluye formatos: 1000, 1.000, 1,000, 1.5, 1,5, etc.
    number_pattern = r'\b\d+(?:[.,]\d+)*\b'
    numbers = re.findall(number_pattern, result)
    for i, number in enumerate(numbers):
        placeholder = f"__NUM_{i}__"
        protected.append((placeholder, number))
        result = result.replace(number, placeholder, 1)
    
    return result, protected


def _restore_entities(text: str, protected: List[Tuple[str, str]]) -> str:
    """
    Restaura las entidades protegidas reemplazando placeholders por valores originales.
    """
    result = text
    for placeholder, original in protected:
        result = result.replace(placeholder, original)
    return result


def apply_glossary_pre(text: str, glossary: Dict[str, str]) -> str:
    """
    Aplica glosario en pre-procesamiento: marca términos ES para protegerlos.
    
    También protege automáticamente URLs, emails y números.
    
    Args:
        text: Texto en español original
        glossary: Diccionario {término_es: término_da}
        
    Returns:
        Texto con términos marcados como [[TERM::<término_es>]]
        
    Estrategia:
        1. Protege URLs, emails y números con placeholders
        2. Ordena términos por longitud descendente (evitar matches parciales)
        3. Búsqueda case-insensitive pero preserva case original
        4. Usa word boundaries para evitar matches parciales
        5. Restaura entidades protegidas
    """
    if not glossary:
        return text
    
    # Proteger URLs, emails, números
    text_protected, entities = _protect_entities(text)
    
    result = text_protected
    
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
    
    # Marcar también las entidades protegidas para que no se traduzcan
    for placeholder, original in entities:
        result = result.replace(placeholder, f"[[KEEP::{original}]]")
    
    return result


def apply_glossary_post(text: str, glossary: Dict[str, str]) -> str:
    """
    Aplica glosario en post-procesamiento: reemplaza marcadores por términos DA.
    
    También restaura entidades protegidas (URLs, emails, números).
    
    Args:
        text: Texto traducido con marcadores [[TERM::...]] y [[KEEP::...]]
        glossary: Diccionario {término_es: término_da}
        
    Returns:
        Texto con marcadores reemplazados por términos daneses y entidades restauradas
        
    Nota:
        - Busca todos los marcadores [[TERM::<algo>]] y los reemplaza por término DA
        - Busca todos los marcadores [[KEEP::<algo>]] y los restaura sin traducir
        - Busca <algo> en el glosario (case-insensitive)
        - Reemplaza con el término danés correspondiente
    """
    result = text
    
    # 1. Procesar marcadores TERM (términos del glosario)
    if glossary:
        # Crear diccionario case-insensitive para lookup
        glossary_lower = {k.lower(): v for k, v in glossary.items()}
        
        # Pattern para encontrar todos los marcadores TERM
        term_pattern = r'\[\[TERM::(.*?)\]\]'
        
        def replace_term_marker(match):
            """Función de reemplazo para cada marcador TERM encontrado."""
            original_term = match.group(1)
            term_lower = original_term.lower()
            
            # Buscar término en glosario (case-insensitive)
            if term_lower in glossary_lower:
                return glossary_lower[term_lower]
            
            # Si no se encuentra, devolver sin marcador (fallback)
            return original_term
        
        result = re.sub(term_pattern, replace_term_marker, result)
    
    # 2. Procesar marcadores KEEP (URLs, emails, números)
    keep_pattern = r'\[\[KEEP::(.*?)\]\]'
    
    def replace_keep_marker(match):
        """Función de reemplazo para cada marcador KEEP encontrado."""
        return match.group(1)  # Restaurar valor original sin traducir
    
    result = re.sub(keep_pattern, replace_keep_marker, result)
    
    # 3. Limpiar cualquier marcador residual (seguridad)
    result = clean_glossary_markers(result)
    
    return result


def clean_glossary_markers(text: str) -> str:
    """
    Limpia cualquier marcador residual que no se haya procesado.
    
    Args:
        text: Texto que puede contener marcadores [[TERM::...]] o [[KEEP::...]]
        
    Returns:
        Texto sin marcadores
        
    Uso:
        Función de seguridad para casos donde el post-procesamiento falla.
    """
    # Limpiar marcadores TERM
    text = re.sub(r'\[\[TERM::(.*?)\]\]', r'\1', text)
    # Limpiar marcadores KEEP
    text = re.sub(r'\[\[KEEP::(.*?)\]\]', r'\1', text)
    return text

