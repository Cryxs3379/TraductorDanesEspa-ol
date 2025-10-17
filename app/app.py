"""
API REST de traducción Español → Danés usando NLLB + CTranslate2.

Servicio 100% local, gratuito y privado.
"""
import os
import logging
from contextlib import asynccontextmanager
from typing import Union

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse

from app.schemas import TranslateRequest, TranslateResponse
from app.inference import load_model, translate_batch, get_model_info
from app.glossary import apply_glossary_pre, apply_glossary_post


# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestión del ciclo de vida de la aplicación.
    Carga el modelo al inicio y libera recursos al finalizar.
    """
    logger.info("Iniciando aplicación...")
    logger.info("=" * 60)
    
    try:
        # Cargar modelo al inicio
        load_model()
        logger.info("✓ Modelo cargado exitosamente")
        logger.info("=" * 60)
        
        # Mostrar información del modelo
        info = get_model_info()
        logger.info(f"Modelo HF: {info['model_dir']}")
        logger.info(f"Modelo CT2: {info['ct2_dir']}")
        logger.info(f"Idiomas: {info['source_lang']} → {info['target_lang']}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"✗ Error al cargar modelo: {e}")
        logger.error("Asegúrate de haber ejecutado:")
        logger.error("  1. make download")
        logger.error("  2. make convert")
        raise
    
    yield
    
    # Cleanup al finalizar
    logger.info("Finalizando aplicación...")


# Crear instancia de FastAPI
app = FastAPI(
    title="Traductor Español → Danés (NLLB + CTranslate2)",
    description=(
        "Servicio de traducción 100% local, gratuito y privado.\n\n"
        "Utiliza el modelo NLLB (No Language Left Behind) de Meta con "
        "cuantización INT8 via CTranslate2 para inferencia eficiente.\n\n"
        "**Características:**\n"
        "- Sin llamadas a Internet (totalmente offline)\n"
        "- Soporte para glosarios personalizados\n"
        "- Procesamiento batch para múltiples textos\n"
        "- Optimizado para CPU con quantization INT8"
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)


@app.get("/")
async def root():
    """Endpoint raíz con información del servicio."""
    info = get_model_info()
    return {
        "service": "Traductor ES → DA",
        "provider": "nllb-ct2-int8",
        "status": "online" if info["loaded"] else "offline",
        "model": {
            "source_lang": info["source_lang"],
            "target_lang": info["target_lang"],
            "model_dir": info["model_dir"],
            "ct2_dir": info["ct2_dir"]
        },
        "endpoints": {
            "translate": "/translate (POST)",
            "docs": "/docs",
            "health": "/health"
        }
    }


@app.get("/health")
async def health():
    """Endpoint de health check."""
    info = get_model_info()
    
    if not info["loaded"]:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Modelo no cargado"
        )
    
    return {
        "status": "healthy",
        "model_loaded": True
    }


@app.post("/translate", response_model=TranslateResponse)
async def translate(request: TranslateRequest):
    """
    Traduce texto de español a danés.
    
    **Parámetros:**
    - `text`: Texto o lista de textos en español
    - `max_new_tokens`: Máximo de tokens a generar (default: 256)
    - `glossary`: Diccionario opcional de términos ES → DA
    
    **Ejemplo de uso:**
    ```json
    {
        "text": "Hola mundo",
        "max_new_tokens": 256
    }
    ```
    
    **Con glosario:**
    ```json
    {
        "text": "Bienvenido a Acme Corporation",
        "glossary": {
            "Acme": "Acme",
            "Corporation": "Selskab"
        }
    }
    ```
    
    **Returns:**
    - `provider`: Identificador del motor de traducción
    - `source`: Código de idioma origen (spa_Latn)
    - `target`: Código de idioma destino (dan_Latn)
    - `translations`: Lista de traducciones
    """
    try:
        # Normalizar input: siempre trabajar con lista
        texts_to_translate = (
            [request.text] if isinstance(request.text, str) else request.text
        )
        
        if not texts_to_translate:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El campo 'text' no puede estar vacío"
            )
        
        # Aplicar glosario pre-traducción si existe
        if request.glossary:
            logger.info(f"Aplicando glosario con {len(request.glossary)} términos")
            texts_to_translate = [
                apply_glossary_pre(text, request.glossary)
                for text in texts_to_translate
            ]
            logger.debug(f"Textos con glosario aplicado: {texts_to_translate}")
        
        # Traducir
        logger.info(f"Traduciendo {len(texts_to_translate)} texto(s)...")
        translations = translate_batch(
            texts_to_translate,
            max_new_tokens=request.max_new_tokens
        )
        
        # Aplicar glosario post-traducción si existe
        if request.glossary:
            translations = [
                apply_glossary_post(text, request.glossary)
                for text in translations
            ]
            logger.debug(f"Traducciones con glosario post: {translations}")
        
        logger.info(f"✓ Traducción completada exitosamente")
        
        # Construir respuesta
        response = TranslateResponse(
            provider="nllb-ct2-int8",
            source="spa_Latn",
            target="dan_Latn",
            translations=translations
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en traducción: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al traducir: {str(e)}"
        )


@app.get("/info")
async def info():
    """Devuelve información detallada del modelo cargado."""
    model_info = get_model_info()
    return {
        "model": model_info,
        "capabilities": {
            "source_languages": ["spa_Latn"],
            "target_languages": ["dan_Latn"],
            "supports_glossary": True,
            "supports_batch": True,
            "max_batch_size": 32,
            "max_tokens_per_translation": 512
        }
    }


# Manejador de errores global
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Maneja excepciones no capturadas."""
    logger.error(f"Excepción no manejada: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Error interno del servidor",
            "error": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    # Configuración para desarrollo
    uvicorn.run(
        "app.app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Reload complica la carga del modelo
        log_level="info"
    )

