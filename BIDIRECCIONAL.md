# 🔄 TRADUCTOR BIDIRECCIONAL ES↔DA

## ✨ NUEVO: Soporte Bidireccional

El traductor ahora soporta **ambas direcciones**:
- 🇪🇸 → 🇩🇰 **Español → Danés** (predeterminado)
- 🇩🇰 → 🇪🇸 **Danés → Español** (nuevo)

---

## 🚀 USO DESDE API

### Español → Danés (predeterminado)

```bash
curl -X POST http://localhost:8000/translate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hola, ¿cómo estás?",
    "direction": "es-da"
  }'
```

**Respuesta**:
```json
{
  "provider": "nllb-ct2-int8",
  "direction": "es-da",
  "source": "spa_Latn",
  "target": "dan_Latn",
  "translations": ["Hvordan har du det?"]
}
```

### Danés → Español (nuevo)

```bash
curl -X POST http://localhost:8000/translate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hej verden",
    "direction": "da-es"
  }'
```

**Respuesta**:
```json
{
  "provider": "nllb-ct2-int8",
  "direction": "da-es",
  "source": "dan_Latn",
  "target": "spa_Latn",
  "translations": ["Hola mundo"]
}
```

---

## 🌐 USO DESDE UI

1. **Abre la UI**:
   ```
   file:///C:/Users/PTRUJILLO/Desktop/Trujillo/TraductorDanesEspañol/ui/index.html
   ```

2. **Selecciona dirección** en el dropdown arriba:
   - 🇪🇸 Español → 🇩🇰 Danés
   - 🇩🇰 Danés → 🇪🇸 Español

3. **Escribe texto** en el idioma correspondiente

4. **Click "Traducir"**

---

## ⚙️ CARACTERÍSTICAS BIDIRECCIONALES

### Caché Separado por Dirección

```json
// Primera traducción ES→DA
{"text": "Hola", "direction": "es-da"}  → 2000ms

// Segunda vez ES→DA (caché)
{"text": "Hola", "direction": "es-da"}  → 50ms

// Primera vez DA→ES (no usa caché de ES→DA)
{"text": "Hola", "direction": "da-es"}  → 2000ms

// Segunda vez DA→ES (caché)
{"text": "Hola", "direction": "da-es"}  → 50ms
```

**Clave de caché**: `direction||texto_normalizado`

### Post-Procesado Específico

#### ES→DA:
- Fechas: `16/10/2025` → `16.10.2025`
- Formal: `Hola` → `Kære`, `tú` → `De`

#### DA→ES:
- Fechas: `16.10.2025` → `16/10/2025`
- Números: preservados
- Sin formalización (el español no usa De/Sie)

### Glosarios Bidireccionales

```json
{
  "text": "Bienvenido a Acme",
  "direction": "es-da",
  "glossary": {
    "Acme": "Acme"  // Se preserva en ambas direcciones
  }
}
```

---

## 🧪 TESTS

```bash
# Test ES→DA (existentes)
pytest tests/test_translate_smoke.py::test_translate_single_text -v

# Test DA→ES (nuevos)
pytest tests/test_translate_smoke.py::test_danish_to_spanish_simple -v

# Test bidireccional
pytest tests/test_translate_smoke.py::test_bidirectional_consistency -v

# Todos los tests
pytest tests/test_translate_smoke.py -v
```

---

## 📊 EJEMPLOS COMPLETOS

### Email corporativo ES→DA

```json
{
  "text": "Estimado cliente,\n\nGracias por su consulta.\n\nSaludos cordiales,\nPedro",
  "direction": "es-da",
  "formal": true
}
```

**Respuesta**: Estilo formal danés con `Kære`, `De`, `Med venlig hilsen`

### Email corporativo DA→ES

```json
{
  "text": "Kære kunde,\n\nTak for din henvendelse.\n\nMed venlig hilsen,\nPeter",
  "direction": "da-es"
}
```

**Respuesta**: Español estándar con fechas en formato dd/mm/yyyy

### HTML Bidireccional

```json
// ES→DA
{
  "html": "<p>Estimado <strong>cliente</strong>,</p><p>Reunión: 16/10/2025</p>",
  "direction": "es-da",
  "formal": true
}

// DA→ES
{
  "html": "<p>Kære <strong>kunde</strong>,</p><p>Møde: 16.10.2025</p>",
  "direction": "da-es"
}
```

---

## ⚡ RENDIMIENTO

| Dirección | Primera Traducción | Con Caché |
|-----------|-------------------|-----------|
| ES→DA | 1-3s | < 100ms |
| DA→ES | 1-3s | < 100ms |

**No hay diferencia de rendimiento** entre direcciones - usa el mismo modelo NLLB.

---

## 🔧 CAMBIOS TÉCNICOS IMPLEMENTADOS

### Backend:

1. **`app/schemas.py`**: Campo `direction` en requests/responses
2. **`app/inference.py`**: Configuración dinámica de `src_lang` y `tgt_lang`
3. **`app/postprocess_es.py`**: Post-procesado para español (nuevo)
4. **`app/cache.py`**: Clave incluye dirección (`direction||text`)
5. **`app/app.py`**: Endpoints usan `request.direction`

### Frontend:

1. **`ui/index.html`**: Dropdown de selección de dirección
2. **`ui/app.js`**: Direction en body de requests + placeholders dinámicos
3. **`ui/styles.css`**: Estilos para selector

### Tests:

1. **`tests/test_translate_smoke.py`**: 3 nuevos tests DA→ES
2. **`tests/test_postprocess_es.py`**: Tests de post-procesado español

---

## ✅ VERIFICACIÓN

```bash
# 1. Reinicia el servidor
python start_server.py

# 2. Prueba ES→DA
curl -X POST http://localhost:8000/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "Hola mundo", "direction": "es-da"}'

# 3. Prueba DA→ES
curl -X POST http://localhost:8000/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "Hej verden", "direction": "da-es"}'

# 4. Verifica capacidades
curl http://localhost:8000/info | grep supported_directions
```

**Esperado**:
```json
"supported_directions": ["es-da", "da-es"],
"bidirectional": true
```

---

## 🎯 COMPATIBILIDAD

### Requests antiguos (sin `direction`):

```json
{"text": "Hola"}
```

**Resultado**: Usa `"es-da"` por defecto (compatible 100%)

### Requests nuevos:

```json
{"text": "Hej", "direction": "da-es"}
```

**Resultado**: Traduce DA→ES

---

## 🎉 ¡TRADUCTOR BIDIRECCIONAL COMPLETO!

**Ahora puedes**:
- ✅ Traducir correos ES→DA
- ✅ Traducir correos DA→ES
- ✅ Usar glosarios en ambas direcciones
- ✅ Aplicar estilo formal (solo para danés)
- ✅ Caché funciona para ambas direcciones
- ✅ UI con selector visual

**Todo manteniendo**:
- ✅ Privacidad 100%
- ✅ Performance (mismo modelo, sin overhead)
- ✅ Caché inteligente por dirección
- ✅ Validación y post-procesado específico por idioma

---

**📝 Documentación actualizada en:**
- `README.md` - Guía completa
- `LISTO_PARA_USAR.md` - Inicio rápido
- `BIDIRECCIONAL.md` - Este documento

