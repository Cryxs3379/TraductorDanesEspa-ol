# Dockerfile para servicio de traducción ES → DA con NLLB + CTranslate2
# Imagen ligera con Python 3.11

FROM python:3.11-slim

# Metadata
LABEL maintainer="Traductor ES-DA"
LABEL description="Servicio de traducción Español → Danés con NLLB y CTranslate2 (INT8)"
LABEL version="1.0.0"

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instalar dependencias del sistema necesarias
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Directorio de trabajo
WORKDIR /app

# Copiar requirements e instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY app/ ./app/
COPY scripts/ ./scripts/

# Crear directorio para modelos (se debe montar como volumen)
RUN mkdir -p /models

# Variables de entorno para rutas de modelos
# IMPORTANTE: Los modelos NO están incluidos en la imagen
# Debes montarlos como volumen: -v ./models:/models
ENV MODEL_NAME=facebook/nllb-200-distilled-600M \
    MODEL_DIR=/models/nllb-600m \
    CT2_DIR=/models/nllb-600m-ct2-int8 \
    CT2_INTER_THREADS=0 \
    CT2_INTRA_THREADS=0

# Exponer puerto
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health').raise_for_status()" || exit 1

# Comando por defecto
CMD ["uvicorn", "app.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

