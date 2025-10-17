"""
Post-procesado específico para danés.

Normaliza números, fechas y aplica formalización opcional según convenciones danesas.
"""
import re
from typing import Optional


def normalize_numbers_da(text: str) -> str:
    """
    Normaliza números al formato danés.
    
    Danés usa:
    - Punto (.) como separador de miles (opcional)
    - Coma (,) como decimal
    
    Ejemplo: "1.234,56" → mantener así (ya está correcto)
    
    Args:
        text: Texto con posibles números
        
    Returns:
        Texto con números normalizados
    """
    # En danés ya se usa coma decimal, así que no hay mucho que hacer
    # Solo asegurar que decimales tengan coma
    
    # Patrón: número.número (español) → número,número (danés)
    # Pero cuidado con URLs y emails
    
    # Por simplicidad, dejar números como están - el traductor suele mantenerlos bien
    return text


def normalize_dates_da(text: str) -> str:
    """
    Normaliza fechas al formato danés.
    
    Danés usa: dd.mm.yyyy o dd/mm/yyyy
    
    Args:
        text: Texto con posibles fechas
        
    Returns:
        Texto con fechas normalizadas
    """
    # Convertir formato dd/mm/yyyy o dd-mm-yyyy a dd.mm.yyyy (preferido en danés)
    # Patrón: día/mes/año
    text = re.sub(
        r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b',
        r'\1.\2.\3',
        text
    )
    
    # Convertir guiones a puntos
    text = re.sub(
        r'\b(\d{1,2})-(\d{1,2})-(\d{4})\b',
        r'\1.\2.\3',
        text
    )
    
    return text


def formalize_da(text: str) -> str:
    """
    Aplica estilo formal a textos en danés.
    
    Transformaciones:
    - Saludos informales → formales
    - Cierres informales → formales daneses
    - Tuteo → tratamiento formal (De/Dem en lugar de du/dig)
    
    Args:
        text: Texto en danés
        
    Returns:
        Texto formalizado
    """
    # Saludos formales comunes
    # "Hej" → "Kære" (estimado/a) si va seguido de nombre/cliente
    text = re.sub(
        r'\bHej\s+([\w\s]+)',
        r'Kære \1',
        text,
        count=1,  # Solo el primero
        flags=re.IGNORECASE
    )
    
    # Cierres formales
    formalizaciones = {
        # Saludos/despedidas informales → formales
        r'\bHilsen\b': 'Med venlig hilsen',
        r'\bMvh\b': 'Med venlig hilsen',
        r'\bVenlig hilsen\b': 'Med venlig hilsen',
        
        # Tratamiento formal (casos comunes)
        r'\bdu\b': 'De',  # tú → usted
        r'\bdig\b': 'Dem',  # ti/te → a usted
        r'\bdin\b': 'Deres',  # tu/tuyo → su (de usted)
        r'\bdine\b': 'Deres',  # tus → sus
    }
    
    for pattern, replacement in formalizaciones.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    # Capitalizar "De/Dem/Deres" al inicio de oración
    text = re.sub(r'\. (de|dem|deres)\b', lambda m: '. ' + m.group(1).capitalize(), text)
    
    return text


def postprocess_da(text: str, formal: bool = False) -> str:
    """
    Post-procesa texto traducido a danés.
    
    Aplica normalizaciones y opcionalmente formalización.
    
    Args:
        text: Texto traducido a danés
        formal: Si True, aplica estilo formal
        
    Returns:
        Texto post-procesado
    """
    if not text:
        return text
    
    # 1. Normalizar números
    text = normalize_numbers_da(text)
    
    # 2. Normalizar fechas
    text = normalize_dates_da(text)
    
    # 3. Formalizar si se requiere
    if formal:
        text = formalize_da(text)
    
    # 4. Limpieza final: espacios múltiples
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text

