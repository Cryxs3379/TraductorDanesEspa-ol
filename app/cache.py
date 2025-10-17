"""
Caché LRU en memoria para traducciones.

Evita retraducciones de segmentos repetidos (especialmente útil en correos con firmas).
"""
import hashlib
import logging
from functools import lru_cache
from typing import Optional


logger = logging.getLogger(__name__)


class TranslationCache:
    """
    Caché simple LRU para traducciones de segmentos.
    
    Usa sha256 del texto normalizado como clave.
    """
    
    def __init__(self, max_size: int = 1024):
        """
        Inicializa el caché.
        
        Args:
            max_size: Capacidad máxima del caché
        """
        self.max_size = max_size
        self.cache = {}
        self.access_order = []  # Para LRU
        self.hits = 0
        self.misses = 0
    
    def _normalize_key(self, text: str) -> str:
        """
        Normaliza texto para usarlo como clave.
        
        - Lowercase
        - Elimina espacios extras
        - Elimina puntuación variable
        """
        # Normalizar espacios
        normalized = ' '.join(text.split())
        # Lowercase
        normalized = normalized.lower()
        return normalized
    
    def _hash_text(self, text: str) -> str:
        """Genera hash SHA256 del texto."""
        normalized = self._normalize_key(text)
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()[:16]
    
    def get(self, text: str) -> Optional[str]:
        """
        Obtiene traducción del caché si existe.
        
        Args:
            text: Texto original
            
        Returns:
            Traducción si está en caché, None en caso contrario
        """
        key = self._hash_text(text)
        
        if key in self.cache:
            # Mover al final (más reciente)
            self.access_order.remove(key)
            self.access_order.append(key)
            self.hits += 1
            
            logger.debug(f"Cache HIT: {key}")
            return self.cache[key]
        
        self.misses += 1
        logger.debug(f"Cache MISS: {key}")
        return None
    
    def put(self, text: str, translation: str):
        """
        Guarda traducción en el caché.
        
        Args:
            text: Texto original
            translation: Traducción a almacenar
        """
        key = self._hash_text(text)
        
        # Si ya existe, actualizarlo y mover al final
        if key in self.cache:
            self.access_order.remove(key)
        # Si el caché está lleno, eliminar el menos usado
        elif len(self.cache) >= self.max_size:
            oldest = self.access_order.pop(0)
            del self.cache[oldest]
            logger.debug(f"Cache EVICT: {oldest}")
        
        self.cache[key] = translation
        self.access_order.append(key)
        logger.debug(f"Cache PUT: {key}")
    
    def clear(self):
        """Limpia el caché."""
        self.cache.clear()
        self.access_order.clear()
        self.hits = 0
        self.misses = 0
        logger.info("Caché limpiado")
    
    def stats(self) -> dict:
        """Retorna estadísticas del caché."""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.1f}%"
        }


# Instancia global de caché
translation_cache = TranslationCache(max_size=1024)

