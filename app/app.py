"""
API REST de traducción Español → Danés usando NLLB + CTranslate2.

Servicio 100% local, gratuito y privado con arranque resiliente.
"""
import logging
import threading
from contextlib import asynccontextmanager
from typing import Union

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse

from app.settings import settings
from app.startup import model_manager
from app.schemas import (
    TranslateRequest, 
    TranslateResponse,
    TranslateHTMLRequest,
    TranslateHTMLResponse
)
from app.inference import translate_batch
from app.glossary import apply_glossary_pre, apply_glossary_post
from app.email_html import translate_html, sanitize_html


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
    
    Carga el modelo en un hilo separado para no bloquear el arranque del servidor.
    La API estará disponible inmediatamente, reportando estado vía /health.
    """
    logger.info("=" * 70)
    logger.info("Iniciando API de traducción ES → DA")
    logger.info("=" * 70)
    
    # 1. Verificar rutas (rápido, no bloquea)
    logger.info("Verificando rutas del modelo...")
    probe_result = model_manager.probe_paths()
    
    if not probe_result["all_ok"]:
        logger.warning("⚠️  Modelo no disponible")
        logger.warning("La API arrancará de todos modos.")
        logger.warning("Consulta /health para más detalles")
    
    # 2. Cargar modelo en hilo separado (para no bloquear)
    if probe_result["all_ok"]:
        logger.info("Cargando modelo en segundo plano...")
        
        def load_in_background():
            """Carga el modelo sin bloquear el arranque."""
            success = model_manager.load()
            if success:
                logger.info("✓ Modelo listo para usar")
            else:
                logger.error("✗ Fallo al cargar modelo (consulta /health)")
        
        loading_thread = threading.Thread(target=load_in_background, daemon=True)
        loading_thread.start()
        
        logger.info("✓ Servidor arrancando (modelo cargando en paralelo)")
    else:
        logger.warning("✗ Modelo no se cargará automáticamente")
        logger.warning(f"   Razón: {model_manager.last_error}")
    
    logger.info("=" * 70)
    logger.info(f"API disponible en http://{settings.HOST}:{settings.PORT}")
    logger.info(f"Documentación: http://{settings.HOST}:{settings.PORT}/docs")
    logger.info(f"Health check: http://{settings.HOST}:{settings.PORT}/health")
    logger.info("=" * 70)
    
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
        "- Traducción de HTML para correos electrónicos\n"
        "- Optimizado para CPU con quantization INT8"
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS desactivado por defecto (seguridad)
# Descomentar solo si necesitas acceso desde UI local
# from fastapi.middleware.cors import CORSMiddleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:*", "file://"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


@app.get("/")
async def root():
    """Endpoint raíz con información del servicio."""
    health_info = model_manager.health()
    
    return {
        "service": "Traductor ES → DA",
        "provider": "nllb-ct2-int8",
        "status": "ready" if health_info["model_loaded"] else "starting",
        "model_loaded": health_info["model_loaded"],
        "endpoints": {
            "translate": "/translate (POST) - Traducir texto simple o batch",
            "translate_html": "/translate/html (POST) - Traducir HTML de correos",
            "health": "/health (GET) - Health check detallado",
            "info": "/info (GET) - Información del modelo",
            "docs": "/docs - Documentación interactiva"
        },
        "help": "Si model_loaded=false, consulta /health para diagnóstico"
    }


@app.get("/health")
async def health():
    """
    Endpoint de health check.
    
    SIEMPRE responde 200, incluso si el modelo no está cargado.
    Usa el campo 'model_loaded' para verificar si el modelo está disponible.
    """
    health_info = model_manager.health()
    
    # Siempre 200 - el servidor está vivo
    return {
        "status": "healthy",  # API está viva
        "model_loaded": health_info["model_loaded"],
        "ready_for_translation": health_info["model_loaded"],
        "last_error": health_info["last_error"],
        "paths": health_info["paths"],
        "config": health_info["config"],
        "load_time_ms": health_info["load_time_ms"]
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
    # Verificar que el modelo esté cargado
    if not model_manager.model_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Modelo no cargado. "
                "Revisa /health para diagnóstico. "
                "Si los modelos no están descargados, ejecuta: "
                "make download && make convert"
            )
        )
    
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
            if not settings.LOG_TRANSLATIONS:
                logger.info(f"Aplicando glosario con {len(request.glossary)} términos")
            texts_to_translate = [
                apply_glossary_pre(text, request.glossary)
                for text in texts_to_translate
            ]
        
        # Traducir
        if not settings.LOG_TRANSLATIONS:
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
        
        if not settings.LOG_TRANSLATIONS:
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


@app.post("/translate/html", response_model=TranslateHTMLResponse)
async def translate_html_endpoint(request: TranslateHTMLRequest):
    """
    Traduce HTML de correos electrónicos de español a danés.
    
    Preserva estructura HTML básica: etiquetas, formato, enlaces, etc.
    
    **Parámetros:**
    - `html`: Contenido HTML del correo
    - `max_new_tokens`: Máximo de tokens a generar por bloque (default: 256)
    - `glossary`: Diccionario opcional de términos ES → DA
    
    **Ejemplo de uso:**
    ```json
    {
        "html": "<p>Hola <strong>mundo</strong></p>",
        "max_new_tokens": 256
    }
    ```
    
    **Returns:**
    - `provider`: Identificador del motor de traducción
    - `source`: Código de idioma origen (spa_Latn)
    - `target`: Código de idioma destino (dan_Latn)
    - `html`: HTML traducido con estructura preservada
    """
    # Verificar que el modelo esté cargado
    if not model_manager.model_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Modelo no cargado. "
                "Revisa /health para diagnóstico. "
                "Si los modelos no están descargados, ejecuta: "
                "make download && make convert"
            )
        )
    
    try:
        if not request.html or not request.html.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El campo 'html' no puede estar vacío"
            )
        
        # Sanitizar HTML de entrada (seguridad)
        html_clean = sanitize_html(request.html)
        
        if not settings.LOG_TRANSLATIONS:
            logger.info(f"Traduciendo HTML ({len(html_clean)} caracteres)...")
        
        # Función de traducción wrapper que aplica glosario
        def translate_with_glossary(texts: list[str]) -> list[str]:
            # Pre-procesamiento con glosario
            if request.glossary:
                texts = [apply_glossary_pre(t, request.glossary) for t in texts]
            
            # Traducir
            translations = translate_batch(texts, max_new_tokens=request.max_new_tokens)
            
            # Post-procesamiento con glosario
            if request.glossary:
                translations = [apply_glossary_post(t, request.glossary) for t in translations]
            
            return translations
        
        # Traducir HTML
        html_translated = translate_html(
            html_clean,
            translate_fn=translate_with_glossary,
            glossary=request.glossary,
            max_new_tokens=request.max_new_tokens
        )
        
        if not settings.LOG_TRANSLATIONS:
            logger.info("✓ HTML traducido exitosamente")
        
        # Construir respuesta
        response = TranslateHTMLResponse(
            provider="nllb-ct2-int8",
            source="spa_Latn",
            target="dan_Latn",
            html=html_translated
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en traducción HTML: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al traducir HTML: {str(e)}"
        )


@app.get("/info")
async def info():
    """Devuelve información detallada del modelo cargado."""
    health_info = model_manager.health()
    
    return {
        "model": {
            "loaded": health_info["model_loaded"],
            "paths": health_info["paths"],
            "config": health_info["config"],
            "load_time_ms": health_info["load_time_ms"]
        },
        "capabilities": {
            "source_languages": ["spa_Latn"],
            "target_languages": ["dan_Latn"],
            "supports_glossary": True,
            "supports_batch": True,
            "supports_html": True,
            "max_batch_size": settings.MAX_BATCH_SIZE,
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
    from app.settings import pick_free_port
    
    # Encontrar puerto libre
    port = pick_free_port(settings.PORT)
    
    logger.info(f"Iniciando servidor en {settings.HOST}:{port}")
    
    # Configuración para desarrollo
    uvicorn.run(
        "app.app:app",
        host=settings.HOST,
        port=port,
        reload=False,  # Reload complica la carga del modelo
        log_level="info"
    )

