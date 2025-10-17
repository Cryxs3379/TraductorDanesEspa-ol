"""
Post-procesado específico para español.

Normaliza números, fechas y formatos al estilo español.
"""
import re


def normalize_dates_es(text: str) -> str:
    """
    Normaliza fechas al formato español.
    
    Español usa: dd/mm/yyyy
    Convierte formato danés (dd.mm.yyyy) a español.
    
    Args:
        text: Texto con posibles fechas
        
    Returns:
        Texto con fechas normalizadas al formato español
    """
    # Convertir formato dd.mm.yyyy (danés) a dd/mm/yyyy (español)
    text = re.sub(
        r'\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b',
        r'\1/\2/\3',
        text
    )
    
    return text


def normalize_numbers_es(text: str) -> str:
    """
    Normaliza números al formato español.
    
    Español usa:
    - Punto (.) como separador de miles
    - Coma (,) como decimal
    
    Args:
        text: Texto con posibles números
        
    Returns:
        Texto con números normalizados
    """
    # En español ya se usa coma decimal similar al danés
    # Generalmente no hay mucho que ajustar
    return text


def postprocess_es(text: str) -> str:
    """
    Post-procesa texto traducido a español.
    
    Aplica normalizaciones específicas del español.
    
    Args:
        text: Texto traducido a español
        
    Returns:
        Texto post-procesado
    """
    if not text:
        return text
    
    # 1. Normalizar fechas
    text = normalize_dates_es(text)
    
    # 2. Normalizar números
    text = normalize_numbers_es(text)
    
    # 3. Limpieza final: espacios múltiples
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text

