# 🔧 Instrucciones para Reiniciar Backend

## Problema Encontrado

Había un bug en `app/app.py` donde la variable `resolved_max_new_tokens` se usaba antes de definirse en el nuevo path de preservación.

## ✅ Solución Aplicada

He movido la inicialización de `resolved_max_new_tokens` ANTES del bloque `if request.preserve_newlines`.

## 📋 Pasos para Aplicar el Fix

### 1. Detener el Backend Actual

En la terminal donde está corriendo `python start_server.py`:
- Presiona **Ctrl+C**

### 2. Reiniciar el Backend

```bash
python start_server.py
```

### 3. Verificar que Funciona

Abre el navegador en:
```
http://localhost:5173
```

Pega este texto con saltos de línea:
```
Hola Juan,

¿Cómo estás?

Saludos,
— Pedro
```

Debería traducirse sin errores ✅

---

## 🧪 Test Rápido Desde PowerShell

```powershell
$body = @{
  direction = "es-da"
  text = "Hola mundo"
  preserve_newlines = $true
} | ConvertTo-Json

Invoke-RestMethod -Method Post `
  -Uri http://localhost:8000/translate `
  -ContentType "application/json" `
  -Body $body
```

**Resultado esperado:**
```json
{
  "provider": "nllb-ct2-int8",
  "direction": "es-da",
  "translations": ["Hej verden"]
}
```

---

## ✅ Verificación Completa

1. **Backend corriendo:** `http://localhost:8000/health` → status 200
2. **Frontend corriendo:** `http://localhost:5173` → UI carga
3. **Traducción funciona:** Pegar texto → traducir → ver resultado
4. **Sin errores:** No error 422, no "referenced before assignment"

---

## 📄 Cambios Realizados

**Archivo:** `app/app.py`

**Línea 300-309** (NUEVO):
```python
# Resolver max_new_tokens ANTES de cualquier procesamiento
resolved_max_new_tokens = resolve_max_new_tokens(
    request.max_new_tokens, 
    texts_to_translate
)

# Debug logging
logger.info(f"🔍 DEBUG - request.max_new_tokens: {request.max_new_tokens}")
logger.info(f"🔍 DEBUG - resolved_max_new_tokens: {resolved_max_new_tokens}")
logger.info(f"🔍 DEBUG - strict_max: {request.strict_max}")
```

Esto asegura que la variable esté definida antes de usarse en el path de `preserve_newlines`.

