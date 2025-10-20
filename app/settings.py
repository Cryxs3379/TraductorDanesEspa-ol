"""
Configuración centralizada del traductor ES→DA.

Centraliza variables de entorno, defaults y utilidades de red.
"""
import os
import socket
from typing import Optional


class Settings:
    """Configuración de la aplicación."""
    
    # Modelo NLLB
    MODEL_NAME: str = os.getenv("MODEL_NAME", "facebook/nllb-200-distilled-600M")
    MODEL_DIR: str = os.getenv("MODEL_DIR", "./models/nllb-600m")
    CT2_DIR: str = os.getenv("CT2_DIR", "./models/nllb-600m-ct2-int8")
    
    # CTranslate2 performance (valores conservadores para evitar cuelgues)
    CT2_INTER_THREADS: int = int(os.getenv("CT2_INTER_THREADS", "4"))
    CT2_INTRA_THREADS: int = int(os.getenv("CT2_INTRA_THREADS", "4"))
    BEAM_SIZE: int = int(os.getenv("BEAM_SIZE", "3"))
    
    # Tokens: auto-calculados por defecto, con elevación server-side y continuación
    MAX_INPUT_TOKENS: int = int(os.getenv("MAX_INPUT_TOKENS", "1024"))      # para no cortar entrada
    DEFAULT_MAX_NEW_TOKENS: int = int(os.getenv("DEFAULT_MAX_NEW_TOKENS", "256"))  # si cliente no envía valor
    MAX_MAX_NEW_TOKENS: int = int(os.getenv("MAX_MAX_NEW_TOKENS", "512"))   # hard cap seguro
    CONTINUATION_INCREMENT: int = 128  # tokens extra para continuación automática
    
    # Segmentación automática (cuando entrada > 90% del límite)
    AUTO_SEGMENT_THRESHOLD: float = 0.9
    MAX_SEGMENT_CHARS: int = int(os.getenv("MAX_SEGMENT_CHARS", "1500"))  # aumentado para menos segmentos
    
    # Servidor
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Idiomas FLORES-200
    SOURCE_LANG: str = "spa_Latn"
    TARGET_LANG: str = "dan_Latn"
    
    # Privacidad
    LOG_TRANSLATIONS: bool = os.getenv("LOG_TRANSLATIONS", "false").lower() == "true"
    
    # Post-procesado danés
    FORMAL_DA: bool = os.getenv("FORMAL_DA", "false").lower() == "true"
    
    # Límites
    MAX_BATCH_SIZE: int = int(os.getenv("MAX_BATCH_SIZE", "16"))
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "300"))


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """
    Verifica si un puerto está en uso.
    
    Args:
        port: Puerto a verificar
        host: Host a verificar (default: localhost)
        
    Returns:
        True si el puerto está ocupado, False si está libre
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return False
        except OSError:
            return True


def pick_free_port(preferred: int, max_attempts: int = 10) -> int:
    """
    Encuentra un puerto libre, empezando por el preferido.
    
    Intenta el puerto preferido. Si está ocupado, prueba preferred+1, +2, etc.
    hasta encontrar uno libre o agotar max_attempts.
    
    Args:
        preferred: Puerto preferido
        max_attempts: Máximo de intentos
        
    Returns:
        Puerto libre encontrado
        
    Raises:
        RuntimeError: Si no se encuentra ningún puerto libre
    """
    for offset in range(max_attempts):
        port = preferred + offset
        if not is_port_in_use(port):
            if offset > 0:
                print(f"⚠️  Puerto {preferred} ocupado, usando {port}")
            return port
    
    raise RuntimeError(
        f"No se pudo encontrar un puerto libre entre {preferred} y {preferred + max_attempts - 1}"
    )


# Instancia global de configuración
settings = Settings()

