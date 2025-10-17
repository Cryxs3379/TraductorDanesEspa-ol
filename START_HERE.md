# 👋 ¡EMPIEZA AQUÍ!

Bienvenido al **Traductor Español → Danés** con NLLB y CTranslate2.

---

## 🎯 ¿Qué es esto?

Un servicio de traducción **100% local, gratuito y privado** que:

- ✅ No necesita Internet (después del setup inicial)
- ✅ Traduce español → danés con IA de última generación
- ✅ Funciona en tu computadora (sin enviar datos a servidores externos)
- ✅ Es completamente gratis y de código abierto

---

## 🚀 Empezar en 3 Pasos

### Paso 1: Instalar

Abre una terminal en esta carpeta y ejecuta:

```bash
make venv
```

Esto crea un entorno virtual e instala todas las dependencias Python.

### Paso 2: Descargar y Preparar el Modelo

```bash
make download
make convert
```

Esto descargará el modelo de traducción (~2.4 GB) y lo optimizará para tu CPU.

**⏱️ Tiempo estimado**: 10-20 minutos (según tu conexión a Internet)

### Paso 3: ¡Ejecutar!

```bash
make run
```

El servidor estará disponible en: **http://localhost:8000**

---

## ✅ Probar que Funciona

En otra terminal, ejecuta:

```bash
make curl-test
```

O abre en tu navegador:
- **Documentación interactiva**: http://localhost:8000/docs
- **Probar traducciones**: Usa la interfaz Swagger en `/docs`

---

## 📚 ¿Qué Sigue?

1. **Lee el README completo**: [`README.md`](README.md)
2. **Prueba los ejemplos**: Carpeta [`examples/`](examples/)
3. **Explora la API**: http://localhost:8000/docs

---

## 🆘 ¿Problemas?

### No funciona el comando `make`

**Windows**: Instala Make para Windows o usa Docker (ver abajo)

**Alternativa sin Make**:
```bash
# En lugar de 'make venv'
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt

# En lugar de 'make download'
python scripts/download_model.py --model facebook/nllb-200-distilled-600M --out models/nllb-600m

# En lugar de 'make convert'
bash scripts/convert_to_ct2.sh --in models/nllb-600m --out models/nllb-600m-ct2-int8

# En lugar de 'make run'
uvicorn app.app:app --host 0.0.0.0 --port 8000
```

### No tengo suficiente RAM

El modelo 600M requiere **~8 GB de RAM**. Si tu computadora tiene menos:

- Cierra otros programas mientras usas el traductor
- Considera usar el servicio en un servidor o máquina virtual

### El puerto 8000 está ocupado

```bash
uvicorn app.app:app --host 0.0.0.0 --port 8001
```

(Luego accede a http://localhost:8001)

---

## 🐳 Alternativa: Usar Docker

Si prefieres Docker:

```bash
# 1. Preparar modelos (en host)
make download
make convert

# 2. Build y run con Docker
make docker-build
make docker-run

# 3. Acceder
curl http://localhost:8000/health
```

---

## 📖 Documentación Completa

| Archivo | Descripción |
|---------|-------------|
| [`README.md`](README.md) | Documentación completa y detallada |
| [`QUICKSTART.md`](QUICKSTART.md) | Guía rápida de 5 minutos |
| [`PROJECT_SUMMARY.md`](PROJECT_SUMMARY.md) | Resumen del proyecto |
| [`FILE_INDEX.md`](FILE_INDEX.md) | Índice de todos los archivos |
| [`TREE.txt`](TREE.txt) | Estructura visual del proyecto |

---

## 💡 Ejemplos Rápidos

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

### Navegador

Abre http://localhost:8000/docs y usa la interfaz Swagger interactiva.

---

## 🎓 Características Avanzadas

Una vez que tengas el servicio funcionando:

- **Glosarios personalizados**: Preserva términos técnicos
- **Traducción batch**: Traduce múltiples textos a la vez
- **Ajuste de performance**: Configura hilos de CPU
- **Modelo más grande**: Usa el modelo 1.3B para mejor calidad

Ver [`README.md`](README.md) para detalles.

---

## ✅ Checklist de Inicio

- [ ] Ejecutar `make venv`
- [ ] Ejecutar `make download` (esperar 10-20 min)
- [ ] Ejecutar `make convert` (esperar 2-5 min)
- [ ] Ejecutar `make run`
- [ ] Probar en http://localhost:8000/docs
- [ ] Leer README.md completo
- [ ] Explorar ejemplos en `examples/`

---

## 🎉 ¡Listo!

Ahora tienes un traductor ES→DA profesional, local y gratuito.

**¿Necesitas ayuda?** Lee [`README.md`](README.md) o verifica `make info`

**¡Disfruta traduciendo! 🇪🇸→🇩🇰**

