# 🚀 Inicio Rápido - Traductor ES→DA

## ✅ CAMBIOS APLICADOS (Sistema Robusto)

### Mejoras Implementadas:

1. **✅ CORS habilitado** - La UI funciona desde `file://` o `localhost`
2. **✅ Sin dependencia de Torch** - Tokenización con listas de IDs (más ligero)
3. **✅ Warmup eliminado** - No más cuelgues en Windows
4. **✅ Parámetros conservadores** - `beam_size=3`, `max_new_tokens=192`
5. **✅ Timeout en UI** - 60 segundos con AbortController
6. **✅ Arranque resiliente** - Servidor arranca aunque el modelo tarde

---

## 🎯 CÓMO USARLO AHORA

### Paso 1: Reiniciar el servidor

**En la ventana donde está corriendo**, presiona **Ctrl+C** para detenerlo.

Luego reinicia:
```bash
python start_server.py
```

### Paso 2: Esperar a que el modelo cargue

Verás en los logs:
```
INFO:app.startup:✓ Modelo CT2 cargado
INFO:app.startup:Omitiendo warmup (puede causar hang en Windows)
INFO:app.startup:✓ Modelo listo - primera traducción será ~2s más lenta
INFO:app.startup:======================================================================
INFO:app.startup:✓ Modelo cargado exitosamente (3.5s)
INFO:app.startup:======================================================================
INFO:app.startup:✓ Modelo listo para usar
```

**Total: ~5-8 segundos** (antes se colgaba en el warmup)

### Paso 3: Ir al navegador

Abre: **http://localhost:8000/docs**

---

## 🧪 PRUEBA RÁPIDA

### En /docs (Swagger):

1. Expande **POST /translate**
2. Click en **"Try it out"**
3. Pega esto:
   ```json
   {
     "text": "Hola, ¿cómo estás?"
   }
   ```
4. Click en **"Execute"**

**Debería devolver en ~2-3 segundos:**
```json
{
  "provider": "nllb-ct2-int8",
  "source": "spa_Latn",
  "target": "dan_Latn",
  "translations": [
    "Hvordan har du det?"
  ]
}
```

---

## 🌐 USAR LA UI WEB

Abre en tu navegador:
```
file:///C:/Users/PTRUJILLO/Desktop/Trujillo/TraductorDanesEspañol/ui/index.html
```

**Características:**
- ✅ CORS ya configurado - funciona desde file://
- ✅ Timeout de 60s - no se queda colgado
- ✅ Indicador de estado - verifica conexión automáticamente
- ✅ Panel de glosario - protege términos corporativos

---

## ⚙️ CONFIGURACIÓN RECOMENDADA

Crea un archivo `.env`:
```bash
cp env.example .env
```

Ajusta si es necesario:
```ini
BEAM_SIZE=3
MAX_NEW_TOKENS=192
CT2_INTER_THREADS=4
CT2_INTRA_THREADS=4
```

---

## ❓ Problemas Comunes

### "503 Service Unavailable"
- El modelo aún está cargando
- Espera 5-10 segundos y reintenta
- Verifica `/health` - debe decir `model_loaded: true`

### "Timeout"
- Tu texto es muy largo
- Reduce `max_new_tokens` a 128
- O divide el texto en partes más pequeñas

### CORS Error en UI
- Ya está solucionado con los cambios
- Si persiste, verifica que la URL en Settings sea `http://localhost:8000`

---

## 🎉 ¡TODO LISTO!

El sistema ahora es **robusto, rápido y no se cuelga**.

**Próximo paso**: Reinicia el servidor y prueba en `/docs` 🚀

