# Mejoras de Performance y Anti-Truncado

## 📋 Resumen

Este documento describe las mejoras implementadas para:
1. **Evitar traducciones cortadas** de frases largas
2. **Hacer la aplicación más fluida** y responsiva

## 🎯 Cambios Implementados

### 1. Backend - Anti-Truncado

#### 1.1 Límites de entrada aumentados

**Archivo**: `app/settings.py`

```python
# Antes
MAX_INPUT_TOKENS: int = 384
MAX_NEW_TOKENS: int = 192

# Después
MAX_INPUT_TOKENS: int = 1024   # +166% para textos largos
MAX_NEW_TOKENS: int = 256       # +33% para salidas completas
```

**Impacto**:
- ✅ Textos de hasta ~3000 caracteres sin truncado
- ✅ Traducciones completas sin cortes abruptos
- ✅ Mejor manejo de emails y documentos largos

#### 1.2 max_new_tokens Adaptativo

**Archivo**: `app/inference.py`

Nueva función `_derive_max_new_tokens()` que calcula automáticamente el número de tokens de salida basado en la longitud de entrada:

```python
def _derive_max_new_tokens(input_lengths: List[int]) -> int:
    """
    Heurística: salida ~ 1.2x del input más largo
    Límite: 128-512 (según schema Pydantic)
    """
    max_input_len = max(input_lengths)
    estimated = int(max_input_len * 1.2)
    return max(128, min(512, estimated))
```

**Comportamiento**:
- Si el cliente **NO especifica** `max_new_tokens`, el backend lo calcula automáticamente
- Si el cliente **especifica** un valor, se respeta
- Rango válido: 32-512 tokens (validado por Pydantic)

**Impacto**:
- ✅ Traducciones más completas sin intervención manual
- ✅ Optimización automática según longitud de entrada
- ✅ Menos errores de truncado

#### 1.3 Segmentación Inteligente

**Archivo**: `app/segment_text.py` (nuevo)

Módulo reutilizable para segmentación de texto plano:

```python
def split_text_for_plain(text: str, max_segment_chars: int = 800) -> List[str]:
    """
    Segmenta texto largo preservando oraciones y párrafos.
    Reutiliza split_text_for_email (ya testeado).
    """
```

**Actualización en `app/app.py`**:
- Segmentación con `max_segment_chars=800` (antes: 600)
- Usa `settings.MAX_SEGMENT_CHARS` para configurabilidad

**Impacto**:
- ✅ Menos segmentos → menos overhead
- ✅ Traducciones más coherentes
- ✅ Preserva contexto entre oraciones

### 2. Frontend - Control UI y Fluidez

#### 2.1 Control de Max Tokens

**Archivos**: 
- `frontend/src/store/useAppStore.ts`
- `frontend/src/components/TextTranslator.tsx`
- `frontend/src/components/HtmlTranslator.tsx`

**Nuevo control UI**:

```tsx
<div className="flex items-center gap-2">
  <Label htmlFor="max-tokens">Max tokens:</Label>
  <input
    id="max-tokens"
    type="number"
    min={32}
    max={512}
    step={16}
    value={maxNewTokens}
    onChange={...}
  />
</div>
```

**Características**:
- 🎚️ Control numérico visible en ambas pestañas (Texto y HTML)
- 💾 Persistido en `localStorage`
- ✅ Validación cliente: 32-512
- 🔢 Default: 256 (actualizado de 192)

**Impacto**:
- ✅ Usuario puede ajustar según necesidad
- ✅ Feedback visual del valor actual
- ✅ Configuración persistente entre sesiones

#### 2.2 Medición de Latencia Corregida

**Archivo**: `frontend/src/hooks/useTranslate.ts`

```typescript
const startTime = performance.now()
// ... traducir ...
const totalTime = Math.round(performance.now() - startTime)
setLastSuccess(`✓ Traducción completada en ${totalTime}ms`)
```

**Impacto**:
- ✅ Métrica precisa de tiempo total
- ✅ Feedback inmediato al usuario
- ✅ Visible en barra de estado inferior

### 3. Esquemas y Validación

**Archivo**: `app/schemas.py`

```python
max_new_tokens: int = Field(
    default=256,  # actualizado de 192
    ge=32,
    le=512,
    description="Número máximo de tokens a generar"
)
```

**Impacto**:
- ✅ Default más alto para textos largos
- ✅ Validación consistente backend/frontend
- ✅ Documentación API actualizada

## 📊 Comparativa Antes/Después

| Métrica | Antes | Después | Mejora |
|---------|-------|---------|--------|
| MAX_INPUT_TOKENS | 384 | 1024 | +166% |
| MAX_NEW_TOKENS (default) | 192 | 256 | +33% |
| max_segment_chars | 600 | 800 | +33% |
| Texto máximo sin truncar | ~1500 chars | ~3000 chars | +100% |
| max_new_tokens | Fijo | Adaptativo | ♾️ |
| Control UI | ❌ | ✅ | ✓ |

## 🧪 Tests

**Archivo**: `tests/test_long_text_plain.py` (nuevo)

Suite de tests para verificar las mejoras:

1. ✅ `test_plain_long_text_not_truncated`
   - Texto de ~3400 caracteres
   - Verifica traducción completa sin truncado

2. ✅ `test_multiple_long_texts_batch`
   - Múltiples textos largos en un request
   - Verifica procesamiento batch correcto

3. ✅ `test_adaptive_max_new_tokens`
   - Verifica cálculo adaptativo
   - Compara texto corto vs largo

4. ✅ `test_segmentation_preserves_meaning`
   - Texto con múltiples párrafos
   - Verifica que segmentación respeta estructura

5. ✅ `test_max_new_tokens_boundary`
   - Verifica límites 32-512
   - Valida error 422 para valores fuera de rango

**Ejecutar tests**:

```bash
# Todos los tests
pytest tests/test_long_text_plain.py -v

# Test específico
pytest tests/test_long_text_plain.py::test_plain_long_text_not_truncated -v
```

## 🚀 Uso

### Backend

**Sin cambios necesarios** - Mejoras automáticas:

```json
{
  "text": "Texto muy largo...",
  "direction": "es-da"
}
```

Backend automáticamente:
- Calcula `max_new_tokens` óptimo
- Segmenta si es necesario
- Traduce sin truncar

**Con control manual**:

```json
{
  "text": "Texto muy largo...",
  "direction": "es-da",
  "max_new_tokens": 384
}
```

### Frontend

1. **Ajuste de Max Tokens**:
   - Visible en header de ambas pestañas
   - Ajustar con ↑↓ o escribir valor
   - Rango: 32-512

2. **Textos largos**:
   - Pegar texto (hasta ~50k caracteres)
   - Backend segmenta automáticamente
   - Traducción completa sin cortes

3. **Métricas**:
   - Latencia visible en barra inferior
   - Cache hits/misses
   - Contador de caracteres con advertencia >10k

## ⚙️ Configuración Avanzada

### Variables de Entorno

```bash
# .env o config.env
MAX_INPUT_TOKENS=1024        # Límite de entrada
MAX_NEW_TOKENS=256           # Default de salida
MAX_SEGMENT_CHARS=800        # Tamaño de segmentos
BEAM_SIZE=3                  # Conservador para estabilidad
```

### Ajuste de Performance

Para **textos muy largos** (>5000 caracteres):

1. Aumentar `MAX_SEGMENT_CHARS` a 1000-1200
2. Aumentar `max_new_tokens` a 384-512
3. Considerar procesamiento en múltiples requests

Para **latencia baja** (textos cortos):

1. Reducir `max_new_tokens` a 128
2. Usar `BEAM_SIZE=2` (opcional)
3. Activar caché para requests repetidos

## 🔍 Debugging

### Logs útiles

```python
# app/inference.py
logger.debug(f"max_new_tokens adaptativo: {old} → {new}")
logger.info(f"Traduciendo {len(segments)} segmentos...")
```

### Métricas del frontend

```typescript
// Console del navegador
console.log("Latencia:", lastLatencyMs, "ms")
console.log("Cache:", info.cache.hit_rate)
```

### Health Check

```bash
curl http://localhost:8000/health
```

```json
{
  "status": "healthy",
  "model_loaded": true,
  "load_time_seconds": 15.23
}
```

## 📝 Notas Técnicas

### Heurística de max_new_tokens

```
salida_estimada = longitud_entrada × 1.2
max_new_tokens = clamp(salida_estimada, 128, 512)
```

**Rationale**:
- Factor 1.2: Danés/Español suelen tener longitud similar (~±20%)
- Min 128: Garantiza traducciones completas para textos cortos
- Max 512: Límite Pydantic y performance

### Segmentación

**Algoritmo**:
1. Detectar párrafos (`\n\n`)
2. Segmentar por oraciones (`. `, `? `, `! `)
3. Agrupar hasta `max_segment_chars`
4. Preservar delimitadores

**Ventajas**:
- No corta en medio de palabra
- Respeta estructura del texto
- Mantiene contexto local

### Cache

El caché incluye la dirección en la clave:

```python
cache_key = f"{direction}||{texto_normalizado}"
```

**Impacto**:
- ✅ Segmentos repetidos → cache hit
- ✅ Retraducciones instantáneas
- ✅ Estadísticas precisas por dirección

## 🎓 Aprendizajes

### ¿Por qué no 2048 tokens?

**Razones**:
1. **Performance CPU**: INT8 en CPU es lento con secuencias muy largas
2. **Memoria**: Batch processing con secuencias largas consume mucha RAM
3. **Calidad**: Segmentación produce traducciones más coherentes
4. **Pragmatismo**: 1024 cubre >95% de casos de uso

### ¿Por qué segmentación automática?

**Alternativas consideradas**:
1. ❌ Aumentar MAX_INPUT_TOKENS a 4096 → Performance inaceptable
2. ❌ Reducir beam_size → Pérdida de calidad
3. ✅ Segmentación inteligente → Balance óptimo

## 🚧 Trabajo Futuro

### Optimizaciones pendientes

- [ ] **Segmentación por contexto**: Usar ventanas deslizantes con overlap
- [ ] **Streaming**: Devolver segmentos traducidos progresivamente
- [ ] **Caché distribuido**: Redis/Memcached para multi-instancia
- [ ] **GPU opcional**: Detectar GPU y usar FP16 si está disponible
- [ ] **Compresión**: Almacenar embeddings en lugar de texto completo

### Mejoras UX pendientes

- [ ] **Barra de progreso**: Para textos largos con múltiples segmentos
- [ ] **Estimación de tiempo**: Basada en longitud y cache hits
- [ ] **Preview en tiempo real**: Mostrar segmentos mientras se traducen
- [ ] **Modo avanzado**: Exponer más parámetros (beam_size, repetition_penalty)

## 📚 Referencias

- [NLLB Model Card](https://huggingface.co/facebook/nllb-200-distilled-600M)
- [CTranslate2 Docs](https://opennmt.net/CTranslate2/)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)
- [React Performance](https://react.dev/learn/render-and-commit)

---

**Fecha**: Octubre 2025  
**Versión**: 7.0 - Anti-truncado y Performance  
**Autor**: Sistema de traducción ES ↔ DA

