# 📑 Índice de Archivos del Proyecto

**Total de archivos**: 28+ archivos

---

## 📂 Estructura Completa

### `/` - Raíz del Proyecto

| Archivo | Descripción | Tipo |
|---------|-------------|------|
| `README.md` | Documentación principal del proyecto | Docs |
| `QUICKSTART.md` | Guía de inicio rápido (5 minutos) | Docs |
| `PROJECT_SUMMARY.md` | Resumen ejecutivo del proyecto | Docs |
| `CONTRIBUTING.md` | Guía para contribuidores | Docs |
| `CHANGELOG.md` | Historial de cambios | Docs |
| `FILE_INDEX.md` | Este archivo - índice de archivos | Docs |
| `requirements.txt` | Dependencias Python | Config |
| `Dockerfile` | Imagen Docker del servicio | DevOps |
| `.dockerignore` | Exclusiones para build Docker | DevOps |
| `.gitignore` | Exclusiones para Git | Config |
| `Makefile` | Automatización de tareas (20+ comandos) | DevOps |
| `env.example` | Variables de entorno (ejemplo simple) | Config |
| `config.env.example` | Variables de entorno (ejemplo detallado) | Config |

---

### `/app` - Aplicación Principal

| Archivo | Descripción | LOC | Tipo |
|---------|-------------|-----|------|
| `__init__.py` | Package marker | 1 | Core |
| `app.py` | FastAPI app y endpoints | ~250 | Core |
| `schemas.py` | Modelos Pydantic (request/response) | ~80 | Core |
| `inference.py` | Motor CTranslate2 + tokenizador | ~200 | Core |
| `glossary.py` | Funciones de glosario pre/post | ~120 | Core |

**Total app/**: ~650 líneas de código

---

### `/scripts` - Scripts de Setup

| Archivo | Descripción | LOC | Tipo |
|---------|-------------|-----|------|
| `__init__.py` | Package marker | 1 | Utility |
| `download_model.py` | Descarga modelos desde HuggingFace | ~150 | Utility |
| `convert_to_ct2.sh` | Conversión a CTranslate2 INT8 | ~100 | Utility |
| `check_system.py` | Verificación del sistema | ~200 | Utility |

**Total scripts/**: ~450 líneas de código

---

### `/tests` - Tests Automatizados

| Archivo | Descripción | LOC | Tipo |
|---------|-------------|-----|------|
| `__init__.py` | Package marker | 1 | Test |
| `test_translate_smoke.py` | Smoke tests con pytest | ~250 | Test |

**Total tests/**: ~250 líneas de código

---

### `/examples` - Ejemplos de Uso

| Archivo | Descripción | LOC | Tipo |
|---------|-------------|-----|------|
| `README.md` | Documentación de ejemplos | ~80 | Docs |
| `basic_usage.py` | Ejemplos síncronos (requests) | ~150 | Example |
| `async_usage.py` | Ejemplos asíncronos (aiohttp) | ~120 | Example |
| `curl_examples.sh` | Ejemplos con cURL | ~100 | Example |

**Total examples/**: ~450 líneas

---

### `/models` - Modelos (Generado)

| Archivo | Descripción | Tipo |
|---------|-------------|------|
| `README.md` | Instrucciones para modelos | Docs |
| `nllb-600m/` | Modelo HF (generado con `make download`) | Model |
| `nllb-600m-ct2-int8/` | Modelo CT2 (generado con `make convert`) | Model |

**Nota**: Los modelos no están en Git (.gitignore). Se generan localmente.

---

## 📊 Estadísticas del Proyecto

### Por Tipo de Archivo

| Tipo | Cantidad | Descripción |
|------|----------|-------------|
| **Python (.py)** | 10 | Código de aplicación, tests, scripts |
| **Markdown (.md)** | 7 | Documentación |
| **Shell (.sh)** | 1 | Script de conversión |
| **Config** | 5 | Docker, Make, requirements, env |
| **Total** | **23+** | Sin contar modelos generados |

### Por Categoría

| Categoría | Archivos | LOC Estimado |
|-----------|----------|--------------|
| **Core App** | 5 | ~650 |
| **Scripts** | 4 | ~450 |
| **Tests** | 2 | ~250 |
| **Examples** | 4 | ~450 |
| **Documentación** | 7 | ~1,500 |
| **Config** | 5 | ~150 |
| **Total** | **27** | **~3,450** |

---

## 🎯 Archivos Clave por Función

### Para Empezar Rápido

1. `QUICKSTART.md` - Guía de 5 minutos
2. `README.md` - Documentación completa
3. `Makefile` - Comandos automatizados

### Para Desarrollo

1. `app/app.py` - Endpoint principal
2. `app/inference.py` - Lógica de traducción
3. `app/schemas.py` - Modelos de datos
4. `tests/test_translate_smoke.py` - Tests

### Para Deployment

1. `Dockerfile` - Imagen Docker
2. `requirements.txt` - Dependencias
3. `Makefile` - Build y deploy
4. `config.env.example` - Configuración

### Para Aprender

1. `examples/basic_usage.py` - Uso básico
2. `examples/async_usage.py` - Uso avanzado
3. `examples/curl_examples.sh` - CLI
4. `README.md` - Conceptos técnicos

---

## 🔍 Búsqueda Rápida

### "¿Dónde está...?"

| Busco... | Archivo | Línea |
|----------|---------|-------|
| Endpoint `/translate` | `app/app.py` | ~80 |
| Carga del modelo CT2 | `app/inference.py` | ~35 |
| Lógica de traducción | `app/inference.py` | ~105 |
| Glosario pre-processing | `app/glossary.py` | ~20 |
| Glosario post-processing | `app/glossary.py` | ~55 |
| Modelos Pydantic | `app/schemas.py` | Todo |
| Descarga de modelos | `scripts/download_model.py` | ~35 |
| Conversión CT2 | `scripts/convert_to_ct2.sh` | ~50 |
| Tests principales | `tests/test_translate_smoke.py` | Todo |
| Comando `make run` | `Makefile` | ~75 |
| Configuración Docker | `Dockerfile` | Todo |

---

## 📖 Flujo de Lectura Sugerido

### Para Nuevos Usuarios

1. `QUICKSTART.md` - Empezar rápido
2. `README.md` (secciones básicas)
3. `examples/basic_usage.py` - Ver ejemplos
4. `app/app.py` - Entender endpoints

### Para Desarrolladores

1. `PROJECT_SUMMARY.md` - Visión general
2. `app/schemas.py` - Modelos de datos
3. `app/inference.py` - Motor de traducción
4. `app/glossary.py` - Lógica de glosarios
5. `tests/test_translate_smoke.py` - Casos de uso

### Para DevOps

1. `Dockerfile` - Container setup
2. `Makefile` - Comandos de deployment
3. `scripts/download_model.py` - Pipeline de modelos
4. `scripts/convert_to_ct2.sh` - Conversión
5. `config.env.example` - Variables de entorno

---

## 🛠️ Archivos Modificables

### Configuración del Usuario

- `config.env.example` → `.env` (crear y editar)
- `Makefile` - Variables en la parte superior
- `Dockerfile` - Variables de entorno

### Extensión del Código

- `app/app.py` - Añadir nuevos endpoints
- `app/schemas.py` - Nuevos modelos
- `app/glossary.py` - Mejorar lógica de glosarios
- `tests/test_translate_smoke.py` - Más tests

---

## 🚫 Archivos NO Modificables (Generados)

- `/models/*` - Generados por scripts
- `__pycache__/` - Cache de Python
- `.pytest_cache/` - Cache de pytest

---

## 📦 Archivos para Distribución

### Incluir en Git

- ✅ Todos los `.py`
- ✅ Todos los `.md`
- ✅ `requirements.txt`
- ✅ `Dockerfile`, `Makefile`
- ✅ `.gitignore`, `.dockerignore`
- ✅ Scripts en `/scripts`
- ✅ Examples en `/examples`

### NO Incluir en Git (`.gitignore`)

- ❌ `/models/*` - Demasiado grandes
- ❌ `/venv/` - Entorno virtual
- ❌ `__pycache__/` - Cache
- ❌ `.env` - Configuración local

### Incluir en Docker Build

- ✅ `/app/*`
- ✅ `/scripts/*`
- ✅ `requirements.txt`
- ❌ `/models/*` - Montar como volumen
- ❌ `/tests/*` - No necesario en producción

---

## 🎯 Conclusión

Este proyecto está **completamente estructurado** con:

- ✅ **5 módulos core** (app/)
- ✅ **4 scripts utility** (scripts/)
- ✅ **2 archivos de tests** (tests/)
- ✅ **4 ejemplos** (examples/)
- ✅ **7 documentos** (*.md)
- ✅ **5 archivos de config** (Docker, Make, requirements, env)

**Total**: ~3,450 líneas de código + documentación extensa

---

Última actualización: 16 de Octubre, 2025

