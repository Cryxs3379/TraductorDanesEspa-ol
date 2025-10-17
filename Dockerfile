# =============================================================================
# Dockerfile para servicio de traducción ES → DA con NLLB + CTranslate2
# =============================================================================
# Imagen ligera con Python 3.11, optimizada para inferencia CPU
# 100% local y privado - sin llamadas a Internet en runtime

FROM python:3.11-slim

# Metadata
LABEL maintainer="Traductor ES-DA"
LABEL description="Servicio de traducción Español → Danés con NLLB y CTranslate2 (INT8)"
LABEL version="1.0.0"
LABEL privacy="Totalmente offline - sin telemetría ni llamadas externas"

# =============================================================================
# Variables de entorno
# =============================================================================
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# =============================================================================
# Instalar dependencias del sistema
# =============================================================================
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# =============================================================================
# Configurar aplicación
# =============================================================================
WORKDIR /app

# Copiar requirements e instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY app/ ./app/
COPY scripts/ ./scripts/
COPY ui/ ./ui/

# Crear directorio para modelos (se debe montar como volumen)
RUN mkdir -p /models

# =============================================================================
# Variables de entorno para rutas de modelos
# =============================================================================
# IMPORTANTE: Los modelos NO están incluidos en la imagen Docker
# Debes descargarlos en el host y montarlos como volumen:
#   docker run -v ./models:/models:ro ...
#
# El sufijo :ro (read-only) es opcional pero recomendado para seguridad

ENV MODEL_NAME=facebook/nllb-200-distilled-600M \
    MODEL_DIR=/models/nllb-600m \
    CT2_DIR=/models/nllb-600m-ct2-int8 \
    CT2_INTER_THREADS=0 \
    CT2_INTRA_THREADS=0 \
    BEAM_SIZE=4

# =============================================================================
# Configuración de privacidad
# =============================================================================
# Estos valores garantizan que NO se registren textos sensibles
ENV LOG_TRANSLATIONS=false \
    LOG_LEVEL=INFO

# =============================================================================
# Red y seguridad
# =============================================================================
# Exponer puerto (solo necesario si permites acceso desde fuera del contenedor)
EXPOSE 8000

# Health check (verifica que el modelo está cargado y el API responde)
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()" || exit 1

# Usuario no-root para mayor seguridad (opcional pero recomendado)
# Descomenta las siguientes líneas si quieres ejecutar como usuario no-root:
# RUN useradd -m -u 1000 translator && chown -R translator:translator /app
# USER translator

# =============================================================================
# Comando de inicio
# =============================================================================
# Usa 1 worker por defecto (menor consumo de RAM)
# Puedes aumentar workers con: CMD ["uvicorn", "app.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
CMD ["uvicorn", "app.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

# =============================================================================
# Modo Air-Gapped (sin red)
# =============================================================================
# Para ejecutar en modo completamente aislado (sin acceso a red):
#
#   1. Descarga y convierte el modelo PRIMERO en el host:
#      make download && make convert
#
#   2. Construye la imagen Docker normalmente:
#      docker build -t traductor-es-da .
#
#   3. Ejecuta el contenedor SIN acceso a red:
#      docker run -d \
#        --name traductor-es-da \
#        --network none \
#        -v ./models:/models:ro \
#        traductor-es-da
#
#      Nota: Con --network none, el contenedor NO tiene acceso a Internet.
#            Solo podrás acceder al API desde el host usando docker exec.
#
#   4. Para acceso local manteniendo aislamiento:
#      docker run -d \
#        --name traductor-es-da \
#        -p 127.0.0.1:8000:8000 \
#        -v ./models:/models:ro \
#        --cap-drop=ALL \
#        --cap-add=NET_BIND_SERVICE \
#        --read-only \
#        --tmpfs /tmp \
#        traductor-es-da
#
#      Esto permite acceso local (localhost:8000) pero bloquea salida a Internet.

