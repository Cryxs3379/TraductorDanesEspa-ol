"""
Tests para el sistema de caché (cache.py).

Verifica funcionalidad LRU y estadísticas.
"""
import pytest
from app.cache import TranslationCache


def test_cache_basic_put_get():
    """Test básico de put/get."""
    cache = TranslationCache(max_size=10)
    
    cache.put("Hola", "Hej")
    result = cache.get("Hola")
    
    assert result == "Hej"
    assert cache.hits == 1
    assert cache.misses == 0


def test_cache_miss():
    """Test de cache miss."""
    cache = TranslationCache(max_size=10)
    
    result = cache.get("Texto no existe")
    
    assert result is None
    assert cache.misses == 1
    assert cache.hits == 0


def test_cache_normalization():
    """Test que la normalización funciona (case-insensitive, espacios)."""
    cache = TranslationCache(max_size=10)
    
    cache.put("Hola  mundo", "Hej verden")
    
    # Debe encontrar con espacios normalizados
    result = cache.get("Hola mundo")
    assert result == "Hej verden"


def test_cache_lru_eviction():
    """Test de evicción LRU cuando se llena."""
    cache = TranslationCache(max_size=3)
    
    # Llenar caché
    cache.put("A", "A_trans")
    cache.put("B", "B_trans")
    cache.put("C", "C_trans")
    
    # Todos deben estar
    assert cache.get("A") == "A_trans"
    assert cache.get("B") == "B_trans"
    assert cache.get("C") == "C_trans"
    
    # Agregar uno más (debe eliminar el menos usado)
    cache.put("D", "D_trans")
    
    # El más antiguo sin acceso debe haberse eliminado
    assert len(cache.cache) == 3


def test_cache_lru_access_order():
    """Test que el acceso actualiza el orden LRU."""
    cache = TranslationCache(max_size=2)
    
    cache.put("A", "A_trans")
    cache.put("B", "B_trans")
    
    # Acceder A (lo mueve al final)
    cache.get("A")
    
    # Agregar C (debe eliminar B, no A)
    cache.put("C", "C_trans")
    
    # A debe seguir estando
    assert cache.get("A") == "A_trans"
    # C debe estar
    assert cache.get("C") == "C_trans"


def test_cache_update_existing():
    """Test de actualización de entrada existente."""
    cache = TranslationCache(max_size=10)
    
    cache.put("Hola", "Hej v1")
    cache.put("Hola", "Hej v2")  # Actualizar
    
    result = cache.get("Hola")
    assert result == "Hej v2"
    
    # No debe haber crecido el caché
    assert len(cache.cache) == 1


def test_cache_stats():
    """Test de estadísticas del caché."""
    cache = TranslationCache(max_size=10)
    
    cache.put("A", "A_trans")
    cache.get("A")  # Hit
    cache.get("B")  # Miss
    cache.get("A")  # Hit
    
    stats = cache.stats()
    
    assert stats["size"] == 1
    assert stats["max_size"] == 10
    assert stats["hits"] == 2
    assert stats["misses"] == 1
    assert "66.7" in stats["hit_rate"] or "66.6" in stats["hit_rate"]  # ~66.7%


def test_cache_clear():
    """Test de limpieza del caché."""
    cache = TranslationCache(max_size=10)
    
    cache.put("A", "A_trans")
    cache.put("B", "B_trans")
    cache.get("A")  # Hit
    
    assert cache.stats()["size"] == 2
    assert cache.stats()["hits"] == 1
    
    cache.clear()
    
    # Todo debe estar limpio
    assert cache.stats()["size"] == 0
    assert cache.stats()["hits"] == 0
    assert cache.stats()["misses"] == 0


def test_cache_with_special_characters():
    """Test con caracteres especiales."""
    cache = TranslationCache(max_size=10)
    
    cache.put("¿Cómo estás?", "Hvordan har du det?")
    result = cache.get("¿Cómo estás?")
    
    assert result == "Hvordan har du det?"


def test_cache_empty_text():
    """Test con texto vacío."""
    cache = TranslationCache(max_size=10)
    
    cache.put("", "empty")
    result = cache.get("")
    
    assert result == "empty"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

