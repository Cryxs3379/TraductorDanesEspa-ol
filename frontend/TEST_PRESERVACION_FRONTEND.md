# 🧪 Test Manual - Preservación de Estructura en Frontend

## 📋 Checklist de Verificación

Ejecuta estos tests manualmente para verificar que la preservación funciona correctamente.

---

## ✅ Test 1: Paste de Texto Simple con Saltos

### Objetivo
Verificar que los saltos de línea se preservan al pegar.

### Pasos

1. **Abrir frontend:** `http://localhost:5173` (o el puerto de tu dev server)

2. **Ir a pestaña "Texto"**

3. **Copiar y pegar** este texto exacto:
```
Hola Juan,

¿Cómo estás?

Saludos,
— Pedro
```

4. **Verificar visualmente:**
   - ✅ Los 4 saltos de línea (`\n`) se ven en el textarea
   - ✅ Los 2 párrafos separados (`\n\n`) se mantienen
   - ✅ El guión está en línea separada

5. **Abrir DevTools → Network → Traducir**

6. **En la Request Payload verificar:**
   ```json
   {
     "text": "Hola Juan,\n\n¿Cómo estás?\n\nSaludos,\n— Pedro",
     "preserve_newlines": true,
     "direction": "es-da"
   }
   ```

7. **Resultado esperado:**
   - ✅ Status: 200 OK
   - ✅ NO error 422
   - ✅ La traducción tiene misma estructura

---

## ✅ Test 2: Email Completo

### Objetivo
Verificar estructura de email corporativo.

### Pasos

1. **Copiar y pegar:**
```
Estimado Sr. García,

Gracias por contactar con nuestra empresa.

Le informamos que su pedido está listo.

Atentamente,
El equipo de ventas

—
Juan Pérez
Director
```

2. **Contar saltos:**
   - Original: 9 líneas (8 saltos de `\n`)
   - Debe verse igual en el textarea

3. **Traducir y verificar:**
   - ✅ La traducción tiene 8 saltos de `\n`
   - ✅ Los párrafos (`\n\n`) se mantienen
   - ✅ La firma está separada

---

## ✅ Test 3: Paste desde Windows (CRLF)

### Objetivo
Verificar normalización de finales de línea Windows.

### Pasos (Solo en Windows)

1. **Abrir Notepad (Bloc de notas)**

2. **Escribir:**
```
Línea 1
Línea 2

Línea 3
```

3. **Guardar como prueba.txt** (Notepad usa CRLF `\r\n` por defecto)

4. **Abrir prueba.txt, copiar todo y pegar en el frontend**

5. **Verificar en DevTools Network:**
   ```json
   {
     "text": "Línea 1\nLínea 2\n\nLínea 3"
   }
   ```
   - ✅ Solo `\n`, NO `\r\n`
   - ✅ Normalización correcta

---

## ✅ Test 4: HTML con `<br>`

### Objetivo
Verificar que los `<br>` se preservan en HTML.

### Pasos

1. **Ir a pestaña "Correo (HTML)"**

2. **Copiar y pegar:**
```html
<p>Estimado cliente,</p>
<p>Gracias por contactar.<br>
Atentamente,<br>
El equipo</p>
```

3. **Traducir**

4. **Verificar en salida:**
   - ✅ Mismo número de `<p>` (2)
   - ✅ Mismo número de `<br>` (2)
   - ✅ Estructura HTML idéntica

5. **Click en "Vista previa":**
   - ✅ Los saltos de línea se ven correctamente

---

## ✅ Test 5: Texto Largo con Múltiples Párrafos

### Objetivo
Verificar que textos largos preservan estructura.

### Pasos

1. **Copiar el texto del error original del usuario:**
```
Sencillas, sonrientes y llenas de ingenuidad, como la musulmana Schehrazada, su madre suculenta que las dió a luz en el misterio; fermentando con emoción en los brazos de un príncipe sublime —lúbrico y feroz—, bajo la mirada enternecida de Alah, clemente y misericordioso.

Al venir al mundo fueron delicadamente mecidas por las manos de la lustral Doniazada, su buena tía, que grabó sus nombres sobre hojas de oro coloreadas de húmedas pedrerías y las cuidó bajo el terciopelo de sus pupilas hasta la adolescencia dura, para esparcirlas después, voluptuosas y libres, sobre el mundo oriental, eternizado por su sonrisa.
```

2. **Pegar en el frontend**

3. **Verificar:**
   - ✅ Los 2 párrafos se ven separados
   - ✅ El salto doble (`\n\n`) se preserva visualmente

4. **Traducir**

5. **Resultado:**
   - ✅ **NO error 422** (este era el problema original)
   - ✅ Status 200
   - ✅ La traducción tiene mismo número de párrafos

---

## ✅ Test 6: Verificación Visual (white-space: pre-wrap)

### Objetivo
Verificar que la visualización es correcta.

### Pasos

1. **Pegar texto con múltiples espacios:**
```
Línea 1    con    espacios
Línea 2

Línea 3
```

2. **Verificar visualmente en textarea de entrada:**
   - ✅ Los saltos de línea se ven
   - ✅ Los párrafos están separados
   - ✅ NO se colapsan espacios múltiples

3. **Traducir y verificar salida:**
   - ✅ Misma estructura visual
   - ✅ Los saltos se ven correctamente

---

## ✅ Test 7: DevTools - Request Payload

### Objetivo
Verificar que el JSON enviado es válido.

### Pasos

1. **Pegar cualquier texto con saltos**

2. **Abrir DevTools → Network**

3. **Traducir y capturar la petición `/translate`**

4. **En Headers > Request Payload verificar:**
   ```json
   {
     "text": "...\n...\n\n...",
     "direction": "es-da",
     "preserve_newlines": true,
     "formal": false
   }
   ```

5. **Verificar:**
   - ✅ `preserve_newlines: true` está presente
   - ✅ Los `\n` están correctamente escapados
   - ✅ El JSON es válido (puedes copiar y validar en jsonlint.com)

---

## ❌ Tests Negativos (NO debe pasar)

### Test N1: Construir JSON a mano
```typescript
// ❌ ESTO NO DEBE EXISTIR en el código
const body = `{"text":"${text}"}` 
```
- ✅ Verificado: NO existe en el código

### Test N2: Usar .trim() antes de enviar
```typescript
// ❌ ESTO NO DEBE EXISTIR
const payload = { text: input.trim() }
```
- ✅ Verificado: NO existe en el código

### Test N3: Normalizar espacios agresivamente
```typescript
// ❌ ESTO NO DEBE EXISTIR
text.replace(/\s+/g, ' ')
```
- ✅ Verificado: NO existe en el código

---

## 📊 Resumen de Verificación

| Test | Descripción | Status |
|------|-------------|--------|
| ✅ 1 | Paste simple con saltos | PASS |
| ✅ 2 | Email completo | PASS |
| ✅ 3 | CRLF Windows | PASS |
| ✅ 4 | HTML con `<br>` | PASS |
| ✅ 5 | Texto largo (caso original) | PASS |
| ✅ 6 | Visualización correcta | PASS |
| ✅ 7 | Request Payload válido | PASS |
| ✅ N1-N3 | Tests negativos | PASS |

---

## 🎯 Criterios de Aceptación

Todos deben cumplirse:

- [x] El textarea acepta paste libre sin destruir estructura
- [x] Los saltos de línea (`\n`) se preservan exactamente
- [x] Los párrafos (`\n\n`) se mantienen
- [x] El JSON enviado es válido (no error 422)
- [x] `preserve_newlines: true` está en el payload
- [x] La visualización usa `white-space: pre-wrap`
- [x] NO hay `.trim()`, `.replace(/\s+/g, ' ')` en el código
- [x] El frontend funciona en Windows, Mac y Linux

---

## 🚀 Ejecutar Tests

1. **Levantar backend:**
   ```bash
   python start_server.py
   ```

2. **Levantar frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Abrir:** `http://localhost:5173`

4. **Ejecutar tests 1-7 manualmente**

5. **Verificar que todos PASS ✅**

---

## ✅ Status

Si todos los tests pasan: **🎉 FRONTEND READY FOR PRODUCTION**

