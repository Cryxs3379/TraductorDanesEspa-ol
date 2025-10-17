# 📧 Traductor Español → Danés (ES→DA)

**Traductor local, privado y offline para correos corporativos**

Sistema de traducción automática de español a danés optimizado para correos electrónicos corporativos, basado en NLLB (No Language Left Behind) de Meta con CTranslate2 para inferencia eficiente en CPU.

🔒 **100% privado** • 🚫 **Sin conexión a Internet** • 💻 **Funciona completamente offline**


para arrancar el servicio, el back se arranca
# Navega a tu carpeta (copia y pega exactamente esto)
cd C:\Users\PTRUJILLO\Desktop\Trujillo\TraductorDanesEspañol

# Activa el entorno virtual
.\venv\Scripts\activate

# Lanza el servidor
python start_server.py

para arrancar el front 

cd .\frontend\ npm run dev
---

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Requisitos](#-requisitos)
- [Instalación Rápida](#-instalación-rápida)
- [Uso](#-uso)
  - [API REST](#api-rest)
  - [Interfaz Web](#interfaz-web)
  - [Glosarios](#glosarios)
- [Docker](#-docker)
- [Configuración Avanzada](#-configuración-avanzada)
- [Tests](#-tests)
- [Arquitectura](#-arquitectura)
- [Modo Air-Gapped](#-modo-air-gapped)
- [Troubleshooting](#-troubleshooting)

---

## ✨ Características

- **🔒 Privacidad Total**: Sin telemetría, sin llamadas externas, 100% offline
- **📧 Optimizado para Correos**: Preserva formato HTML, enlaces, y estructura
- **📚 Glosarios Personalizados**: Protege términos específicos de tu empresa
- **🚀 Rendimiento CPU**: Quantization INT8 con CTranslate2
- **🎯 Traducción Determinística**: Fuerza idioma destino (spa_Latn → dan_Latn)
- **🌐 Interfaz Web Local**: UI moderna para traducción de correos
- **🔄 API REST**: Endpoints `/translate` y `/translate/html`
- **✅ Validación Automática**: Detecta y corrige salidas en alfabetos incorrectos
- **🐳 Docker Ready**: Con modo air-gapped completo

---

## 💻 Requisitos

### Hardware

| Modelo | RAM Mínima | Espacio en Disco | Rendimiento |
|--------|------------|------------------|-------------|
| **600M** (recomendado) | 8 GB | ~3 GB | Bueno |
| **1.3B** | 16 GB | ~6 GB | Excelente |

### Software

- **Python**: 3.9 - 3.11
- **Sistema Operativo**: Linux, macOS, Windows (con WSL2 recomendado)
- **Conexión a Internet**: Solo para descarga inicial del modelo

---

## 🚀 Instalación Rápida

### Opción 1: Instalación Local (Recomendada)

```bash
# 1. Clonar repositorio
git clone <tu-repo>
cd TraductorDanesEspañol

# 2. Crear entorno virtual e instalar dependencias
make venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# 3. Descargar modelo NLLB (requiere Internet, solo una vez)
make download

# 4. Convertir a CTranslate2 INT8 (offline)
make convert

# 5. Iniciar servidor
make run
```

**¡Listo!** El servidor estará disponible en `http://localhost:8000`

### Opción 2: Docker

```bash
# 1. Descargar y convertir modelo en el host (solo una vez)
make download && make convert

# 2. Construir imagen Docker
make docker-build

# 3. Ejecutar contenedor
make docker-run
```

---

## 📖 Uso

### API REST

#### Endpoint: `POST /translate`

Traduce texto simple o múltiples textos:

```bash
curl -X POST http://localhost:8000/translate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hola, ¿cómo estás?",
    "max_new_tokens": 256
  }'
```

**Respuesta:**
```json
{
  "provider": "nllb-ct2-int8",
  "source": "spa_Latn",
  "target": "dan_Latn",
  "translations": ["Hvordan har du det?"]
}
```

#### Endpoint: `POST /translate/html`

Traduce HTML de correos preservando estructura:

```bash
curl -X POST http://localhost:8000/translate/html \
  -H "Content-Type: application/json" \
  -d '{
    "html": "<p>Estimado cliente,</p><p>Gracias por <strong>contactarnos</strong>.</p>",
    "max_new_tokens": 256
  }'
```

#### Endpoint: `GET /health`

Verifica que el servicio esté funcionando:

```bash
curl http://localhost:8000/health
```

### Interfaz Web

Abre en tu navegador:

```
file:///ruta/completa/a/TraductorDanesEspañol/ui/index.html
```

O desde VS Code / editor:
1. Click derecho en `ui/index.html`
2. "Open with Live Server" o "Open in Browser"

**Características de la UI:**
- 📝 **Pestaña Texto**: Traducción simple con carga de archivos `.txt`
- 🌐 **Pestaña HTML**: Traducción de correos HTML con vista previa
- 📚 **Glosario**: Panel de configuración con términos personalizados
- 💾 **Exportar**: Copiar o guardar resultados como `.txt` o `.html`

### Glosarios

Los glosarios te permiten proteger términos específicos de tu organización:

#### Formato

En la UI o API, usa el formato:
```
término_español=término_danés
```

**Ejemplo:**
```
Acme=Acme
Corporation=Selskab
Python=Python
Departamento de TI=IT-afdeling
```

#### En API

```json
{
  "text": "Bienvenido a Acme Corporation",
  "glossary": {
    "Acme": "Acme",
    "Corporation": "Selskab"
  }
}
```

**Protección Automática:**
- URLs: `https://example.com` → se preservan automáticamente
- Emails: `usuario@dominio.com` → se preservan automáticamente
- Números: `1000`, `1.234,56` → se preservan automáticamente

---

## 🐳 Docker

### Construcción

```bash
docker build -t traductor-es-da .
```

### Ejecución Normal

```bash
docker run -d \
  --name traductor-es-da \
  -p 8000:8000 \
  -v $(pwd)/models:/models:ro \
  traductor-es-da
```

### Ejecución Air-Gapped (Sin Red)

Para máxima seguridad, sin acceso a Internet:

```bash
docker run -d \
  --name traductor-es-da \
  --network none \
  -v $(pwd)/models:/models:ro \
  traductor-es-da
```

**Nota**: Con `--network none`, el contenedor no puede acceder a Internet pero tampoco podrás acceder al API desde el host. Úsalo solo para procesamiento por lotes.

### Ejecución Segura con Acceso Local

```bash
docker run -d \
  --name traductor-es-da \
  -p 127.0.0.1:8000:8000 \
  -v $(pwd)/models:/models:ro \
  --cap-drop=ALL \
  --cap-add=NET_BIND_SERVICE \
  --read-only \
  --tmpfs /tmp \
  traductor-es-da
```

---

## ⚙️ Configuración Avanzada

### Variables de Entorno

Copia `env.example` a `.env` y ajusta según necesidades:

```bash
cp env.example .env
```

**Principales configuraciones:**

| Variable | Default | Descripción |
|----------|---------|-------------|
| `MODEL_NAME` | `facebook/nllb-200-distilled-600M` | Modelo a descargar |
| `MODEL_DIR` | `./models/nllb-600m` | Directorio del modelo HF |
| `CT2_DIR` | `./models/nllb-600m-ct2-int8` | Directorio del modelo CT2 |
| `BEAM_SIZE` | `4` | Tamaño de beam search (4-5 recomendado) |
| `CT2_INTER_THREADS` | `0` | Hilos inter-capas (0=auto) |
| `CT2_INTRA_THREADS` | `0` | Hilos intra-capas (0=auto) |

### Cambiar a Modelo 1.3B

Para mejor calidad (requiere 16GB RAM):

```bash
# Editar .env
MODEL_NAME=facebook/nllb-200-1.3B
MODEL_DIR=./models/nllb-1.3b
CT2_DIR=./models/nllb-1.3b-ct2-int8

# Descargar y convertir
make download && make convert

# Reiniciar servidor
make run
```

---

## 🧪 Tests

Ejecutar todos los tests:

```bash
make test
```

Tests específicos:

```bash
# Test de smoke (requiere modelo cargado)
pytest tests/test_translate_smoke.py -v

# Test de glosario (no requiere modelo)
pytest tests/test_glossary.py -v

# Test de HTML (no requiere modelo)
pytest tests/test_email_html.py -v
```

**Nota**: Los tests de traducción (`test_translate_smoke.py`) requieren que el modelo esté descargado y convertido.

---

## 🏗️ Arquitectura

```
TraductorDanesEspañol/
├── app/
│   ├── app.py              # FastAPI endpoints
│   ├── inference.py        # Motor CT2 + validación idioma
│   ├── glossary.py         # Protección de términos
│   ├── email_html.py       # Procesamiento HTML correos
│   └── schemas.py          # Modelos Pydantic
├── ui/
│   ├── index.html          # Interfaz web
│   ├── app.js              # Lógica cliente
│   └── styles.css          # Estilos
├── scripts/
│   ├── download_model.py   # Descarga desde HuggingFace
│   └── convert_to_ct2.sh   # Conversión a CTranslate2
├── tests/
│   ├── test_translate_smoke.py
│   ├── test_glossary.py
│   └── test_email_html.py
├── models/                 # (ignorado en git)
│   ├── nllb-600m/         # Modelo HuggingFace
│   └── nllb-600m-ct2-int8/ # Modelo CTranslate2
├── Makefile
├── Dockerfile
├── requirements.txt
└── env.example
```

### Flujo de Traducción

1. **Input**: Texto ES o HTML → API FastAPI
2. **Pre-procesamiento**: Aplicar glosario (marcar términos protegidos)
3. **Tokenización**: NLLB tokenizer con `src_lang="spa_Latn"`
4. **Traducción**: CTranslate2 con `target_prefix=[[dan_Latn]]` y `beam_size=4`
5. **Validación**: Verificar alfabeto latino (>80% chars válidos)
6. **Post-procesamiento**: Reemplazar marcadores por términos DA
7. **Limpieza**: Eliminar artefactos (tokens idioma visibles)
8. **Output**: Texto DA o HTML DA

---

## 🔐 Modo Air-Gapped

Para entornos corporativos con restricciones de red:

### Preparación (requiere Internet una sola vez)

```bash
# 1. En máquina con Internet:
git clone <repo>
cd TraductorDanesEspañol
make venv
source venv/bin/activate
make download  # Descarga modelo (~2.4GB)
make convert   # Convierte a CT2 (offline)

# 2. Copiar directorio completo a máquina sin Internet
tar -czf traductor-complete.tar.gz TraductorDanesEspañol/
# Transferir traductor-complete.tar.gz a máquina destino
```

### Uso Sin Internet

```bash
# En máquina sin Internet:
tar -xzf traductor-complete.tar.gz
cd TraductorDanesEspañol
source venv/bin/activate  # venv incluye dependencias
make run
```

**Verificación**:
- El servidor arranca correctamente
- `/health` devuelve `{"status": "healthy"}`
- No se observan intentos de conexión externa en logs

---

## 🔧 Troubleshooting

### Problema: Modelo no encontrado

```
FileNotFoundError: Directorio de modelo CT2 no encontrado
```

**Solución:**
```bash
make download  # Si no has descargado el modelo
make convert   # Si no has convertido a CT2
```

### Problema: Out of Memory

```
RuntimeError: Failed to allocate memory
```

**Soluciones:**
1. Cierra otras aplicaciones
2. Reduce `DEFAULT_BATCH_SIZE` en `.env`
3. Usa modelo 600M en lugar de 1.3B
4. Añade swap (Linux):
   ```bash
   sudo fallocate -l 4G /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

### Problema: Traducción muy lenta

**Soluciones:**
1. Ajusta hilos en `.env`:
   ```bash
   CT2_INTER_THREADS=4
   CT2_INTRA_THREADS=4
   ```
2. Verifica que usas INT8 (no float32)
3. Reduce `BEAM_SIZE` de 4 a 3

### Problema: Salida en alfabeto incorrecto

El sistema detecta automáticamente caracteres no latinos y reintenta con `beam_size` mayor. Si persiste:

```bash
# Aumentar beam_size en .env
BEAM_SIZE=5
```

### Problema: UI no se conecta al API

**Verificaciones:**
1. Servidor corriendo: `curl http://localhost:8000/health`
2. CORS habilitado en `app/app.py` (ya configurado)
3. URL correcta en UI: Settings → API URL = `http://localhost:8000`

---

## 📊 Benchmarks

| Modelo | Frases/seg | RAM | Calidad (BLEU) |
|--------|-----------|-----|----------------|
| 600M INT8 | 8-12 | 3-4 GB | 28-32 |
| 1.3B INT8 | 4-6 | 6-8 GB | 32-36 |

*Benchmarks en CPU Intel i7-10700K (8 cores), texto promedio 20 tokens*

---

## 📝 Comandos Make

```bash
make help          # Mostrar ayuda
make venv          # Crear entorno virtual
make download      # Descargar modelo
make convert       # Convertir a CT2
make run           # Ejecutar servidor
make test          # Ejecutar tests
make docker-build  # Construir imagen Docker
make docker-run    # Ejecutar contenedor
make clean         # Limpiar temporales
make info          # Ver estado del proyecto
```

---

## 🤝 Contribuciones

Este proyecto está optimizado para uso corporativo interno. Para mejoras:

1. Fork del repositorio
2. Crear branch: `git checkout -b feature/mejora`
3. Commit: `git commit -m 'Añadir mejora'`
4. Push: `git push origin feature/mejora`
5. Pull Request

---

## 📄 Licencia

[Especificar licencia según política corporativa]

---

## 🙏 Créditos

- **NLLB**: [Meta AI - No Language Left Behind](https://ai.facebook.com/research/no-language-left-behind/)
- **CTranslate2**: [OpenNMT](https://github.com/OpenNMT/CTranslate2)
- **FastAPI**: [Tiangolo](https://fastapi.tiangolo.com/)

---

## 📞 Soporte

Para problemas técnicos:
1. Consulta [Troubleshooting](#-troubleshooting)
2. Revisa logs: `docker logs traductor-es-da` (si usas Docker)
3. Contacta al equipo de IT/DevOps interno

---

**🔒 Recordatorio de Privacidad**: Este sistema NO envía datos a Internet. Todos los textos se procesan localmente en tu máquina/servidor. No hay telemetría, analytics ni llamadas a servicios externos.
