# ⚡ Inicio Rápido - Traductor ES→DA

Guía de 5 minutos para poner en marcha el traductor.

---

## 🎯 Opción 1: Local (Recomendado)

### Paso 1: Instalar Dependencias

```bash
# Crear entorno virtual e instalar paquetes
make venv

# O manualmente
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

### Paso 2: Descargar Modelo

```bash
# Descargar modelo 600M (~2.4 GB, tarda 5-15 min)
make download
```

⏱️ **Tiempo estimado**: 5-15 minutos (según conexión)

### Paso 3: Convertir a CTranslate2

```bash
# Convertir a INT8 (tarda 2-5 min)
make convert
```

⏱️ **Tiempo estimado**: 2-5 minutos

### Paso 4: ¡Ejecutar!

```bash
# Iniciar servidor
make run
```

El servidor estará en: **http://localhost:8000**

### Paso 5: Probar

En otra terminal:

```bash
# Test rápido
curl -X POST http://localhost:8000/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "Hola mundo"}'

# O usar el Makefile
make curl-test
```

**¡Listo!** 🎉

---

## 🐳 Opción 2: Docker

### Requisitos
- Docker instalado
- Modelos descargados (se hace en host)

### Paso 1-3: Preparar Modelos

```bash
# Igual que opción local
make download
make convert
```

### Paso 4: Build y Run

```bash
# Construir imagen
make docker-build

# Ejecutar contenedor
make docker-run
```

### Paso 5: Probar

```bash
curl http://localhost:8000/health
make curl-test
```

**¡Listo con Docker!** 🐳

---

## 📊 Verificar Instalación

```bash
# Ver estado del sistema
make info
```

Deberías ver:
```
✓ Modelo HF descargado: ./models/nllb-600m
✓ Modelo CT2 convertido: ./models/nllb-600m-ct2-int8
✓ Entorno virtual creado
```

---

## 🔧 Solución de Problemas

### "Error: Modelo no encontrado"

```bash
make download
make convert
```

### "Error: Puerto 8000 ocupado"

```bash
# Usar otro puerto
uvicorn app.app:app --port 8001
```

### "Out of memory"

Tu sistema no tiene suficiente RAM. Verifica:

```bash
# Linux/Mac
free -h

# Windows (PowerShell)
Get-CimInstance Win32_OperatingSystem | Select FreePhysicalMemory
```

Necesitas al menos **8 GB RAM** para el modelo 600M.

---

## 📖 Siguientes Pasos

1. **Lee el README completo**: `README.md`
2. **Prueba los ejemplos**: `examples/`
3. **Ejecuta los tests**: `make test`
4. **Explora la API**: http://localhost:8000/docs

---

## 🎓 Uso Básico

### Python

```python
import requests

response = requests.post(
    "http://localhost:8000/translate",
    json={"text": "Hola mundo"}
)

print(response.json()["translations"][0])
# Output: "Hej verden"
```

### cURL

```bash
curl -X POST http://localhost:8000/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "Buenos días"}'
```

### JavaScript/Node

```javascript
const response = await fetch('http://localhost:8000/translate', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({text: 'Hola'})
});

const data = await response.json();
console.log(data.translations[0]);
```

---

## ⚙️ Configuración Avanzada

### Cambiar a Modelo 1.3B (mejor calidad)

```bash
# Editar .env
echo "MODEL_NAME=facebook/nllb-200-1.3B" > .env
echo "MODEL_DIR=./models/nllb-1.3b" >> .env
echo "CT2_DIR=./models/nllb-1.3b-ct2-int8" >> .env

# Descargar y convertir
make download-1.3b
make convert MODEL_DIR=./models/nllb-1.3b CT2_DIR=./models/nllb-1.3b-ct2-int8

# Ejecutar
make run
```

**Nota**: Requiere **16 GB RAM**.

### Usar Glosarios

```python
response = requests.post(
    "http://localhost:8000/translate",
    json={
        "text": "Bienvenido a Python",
        "glossary": {"Python": "Python"}  # Preservar
    }
)
```

---

## 📚 Documentación Completa

- **README.md** - Documentación principal
- **PROJECT_SUMMARY.md** - Resumen del proyecto
- **examples/** - Ejemplos de código
- **http://localhost:8000/docs** - API interactiva

---

## ✅ Checklist de Inicio

- [ ] Instalar dependencias (`make venv`)
- [ ] Descargar modelo (`make download`)
- [ ] Convertir modelo (`make convert`)
- [ ] Ejecutar servidor (`make run`)
- [ ] Probar endpoint (`make curl-test`)
- [ ] Leer documentación (`README.md`)
- [ ] Explorar ejemplos (`examples/`)

---

**¿Problemas?** Revisa `README.md` sección "Troubleshooting" o ejecuta `make info`.

**¡Disfruta traduciendo! 🚀**

