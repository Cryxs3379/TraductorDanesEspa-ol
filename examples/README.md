# Ejemplos de Uso

Esta carpeta contiene ejemplos de cómo usar el API de traducción ES→DA.

## 📁 Archivos

- **`basic_usage.py`** - Ejemplos básicos con requests síncronos
- **`async_usage.py`** - Ejemplos con aiohttp asíncrono
- **`curl_examples.sh`** - Ejemplos con cURL (línea de comandos)

## 🚀 Ejecutar Ejemplos

### Prerequisitos

Asegúrate de que el servidor esté corriendo:

```bash
# Desde la raíz del proyecto
make run

# O manualmente
uvicorn app.app:app --host 0.0.0.0 --port 8000
```

### Ejecutar Python básico

```bash
cd examples
python basic_usage.py
```

### Ejecutar Python asíncrono

```bash
cd examples
python async_usage.py
```

### Ejecutar ejemplos cURL

```bash
cd examples
bash curl_examples.sh
```

## 📚 Dependencias Adicionales

Para los ejemplos asíncronos, necesitas `aiohttp`:

```bash
pip install aiohttp
```

## 🎯 Casos de Uso

### Traducción Simple

```python
import requests

response = requests.post(
    "http://localhost:8000/translate",
    json={"text": "Hola mundo"}
)
print(response.json()["translations"][0])
```

### Traducción Batch

```python
response = requests.post(
    "http://localhost:8000/translate",
    json={
        "text": ["Texto 1", "Texto 2", "Texto 3"]
    }
)
for translation in response.json()["translations"]:
    print(translation)
```

### Con Glosario

```python
response = requests.post(
    "http://localhost:8000/translate",
    json={
        "text": "Bienvenido a Python",
        "glossary": {"Python": "Python"}
    }
)
print(response.json()["translations"][0])
```

## 💡 Tips

- **Batch processing**: Agrupa múltiples textos para mejor throughput
- **Glosarios**: Usa para preservar nombres propios y terminología específica
- **max_new_tokens**: Ajusta según la longitud esperada de la traducción
- **Async**: Usa requests asíncronos para máxima concurrencia

## 🔗 Más Información

Ver el [README principal](../README.md) para documentación completa.

