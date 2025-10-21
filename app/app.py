"""
API REST de traducción Español → Danés usando NLLB + CTranslate2.

Servicio 100% local, gratuito y privado con arranque resiliente.
"""
import logging
import threading
from contextlib import asynccontextmanager
from typing import Union
from datetime import datetime

from fastapi import FastAPI, HTTPException, status, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

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
from app.segment import split_text_for_email, split_html_preserving_structure, rehydrate_html
from app.cache import translation_cache
from app.utils_html import sanitize_html


# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Tiempo de inicio del servidor
SERVER_START_TIME = datetime.now()
VERSION = "1.0.0"


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

# CORS habilitado para UI local (file:// y localhost) - Configuración segura
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",  # Permite file:// y cualquier origen local
        "null",  # Origen file:// se reporta como "null"
        "http://localhost",
        "http://127.0.0.1",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:8001",
        "http://localhost:8002",
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:5173"
    ],
    allow_methods=["GET", "POST", "OPTIONS"],  # Restrict methods
    allow_headers=["Content-Type", "Authorization", "Accept"],  # Restrict headers
    allow_credentials=False,  # Crítico: False cuando allow_origins incluye "*"
    max_age=600  # Cache preflight por 10 minutos
)


# Middleware de seguridad
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """
    Añade cabeceras de seguridad a todas las respuestas.
    
    Configuración robusta para entorno corporativo.
    """
    response = await call_next(request)
    
    # Cabeceras de seguridad estándar
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Cache control para APIs - no cachear respuestas con contenido sensible
    if request.url.path.startswith(("/translate", "/info")):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    else:
        # Para assets estáticos, permitir cache
        response.headers["Cache-Control"] = "public, max-age=300"
    
    # Header de privacidad - no permitir seguimiento
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    
    return response


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


def resolve_max_new_tokens(user_value: Union[int, None], input_texts: list[str]) -> Union[int, None]:
    """
    Resuelve max_new_tokens basado en el valor del usuario y el texto de entrada.
    
    CORREGIDO: No limitar artificialmente cuando usuario no especifica valor.
    
    Args:
        user_value: Valor enviado por el cliente (puede ser None)
        input_texts: Lista de textos de entrada para cálculo adaptativo
        
    Returns:
        max_new_tokens a usar en la traducción
    """
    from app.inference import _derive_max_new_tokens
    
    if user_value is not None and user_value > 0:
        # Usuario especificó un valor: validar mínimo pero NO limitar máximo
        # El límite máximo se maneja en inference.py con la lógica adaptativa
        return max(1, int(user_value))
    
    # Usuario no especificó: None para activar cálculo adaptativo en translate_batch
    # Esto permite que inference.py use su lógica ultra-agresiva
    return None


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
    import time
    start_time = time.time()
    
    # Verificar que el modelo esté cargado
    if not model_manager.model_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "El modelo está cargando o no está disponible. "
                "Espera unos segundos y reintenta. "
                "Consulta /health para diagnóstico detallado."
            )
        )
    
    try:
        # Normalizar input: siempre trabajar con lista
        is_single_text = isinstance(request.text, str)
        texts_to_translate = (
            [request.text] if is_single_text else request.text
        )
        
        if not texts_to_translate or all(not t.strip() for t in texts_to_translate):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El campo 'text' no puede estar vacío"
            )
        
        # Segmentar textos largos automáticamente SOLO si es necesario
        all_segments = []
        segment_map = []  # Para reconstruir después
        
        for idx, text in enumerate(texts_to_translate):
            # Solo segmentar si el texto es muy largo (más de 1500 caracteres)
            # o si se acerca al límite de tokens
            if len(text) > settings.MAX_SEGMENT_CHARS:
                # Texto largo: segmentar
                segments = split_text_for_email(text, max_segment_chars=settings.MAX_SEGMENT_CHARS)
                for seg in segments:
                    all_segments.append(seg)
                    segment_map.append(idx)
            else:
                # Texto corto: traducir completo
                all_segments.append(text)
                segment_map.append(idx)
        
        # Aplicar glosario pre-traducción si existe
        if request.glossary:
            if not settings.LOG_TRANSLATIONS:
                logger.info(f"Aplicando glosario con {len(request.glossary)} términos")
            all_segments = [
                apply_glossary_pre(seg, request.glossary)
                for seg in all_segments
            ]
        
        # Resolver max_new_tokens: usar cálculo adaptativo si no se especifica
        resolved_max_new_tokens = resolve_max_new_tokens(
            request.max_new_tokens, 
            all_segments
        )
        
        # Debug logging para investigar truncado
        logger.info(f"🔍 DEBUG - request.max_new_tokens: {request.max_new_tokens}")
        logger.info(f"🔍 DEBUG - resolved_max_new_tokens: {resolved_max_new_tokens}")
        logger.info(f"🔍 DEBUG - strict_max: {request.strict_max}")
        
        # Traducir con caché y dirección
        if not settings.LOG_TRANSLATIONS:
            logger.info(f"Traduciendo {len(all_segments)} segmento(s) [{request.direction}]...")
        
        segment_translations = translate_batch(
            all_segments,
            direction=request.direction,
            max_new_tokens=resolved_max_new_tokens,
            use_cache=True,
            formal=request.formal or settings.FORMAL_DA,
            strict_max=request.strict_max
        )
        
        # Aplicar glosario post-traducción si existe
        if request.glossary:
            segment_translations = [
                apply_glossary_post(seg, request.glossary)
                for seg in segment_translations
            ]
        
        # Reensamblar segmentos por texto original
        translations = []
        for original_idx in range(len(texts_to_translate)):
            # Encontrar todos los segmentos de este texto
            segs_for_this_text = [
                segment_translations[i] 
                for i, seg_idx in enumerate(segment_map) 
                if seg_idx == original_idx
            ]
            
            if len(segs_for_this_text) == 1:
                # Texto no segmentado: usar traducción directa
                translations.append(segs_for_this_text[0])
            else:
                # Texto segmentado: unir con espacio
                translations.append(' '.join(segs_for_this_text))
        
        # Métricas finales
        elapsed_ms = int((time.time() - start_time) * 1000)
        
        if not settings.LOG_TRANSLATIONS:
            logger.info(
                f"✓ Traducción completada: {len(texts_to_translate)} textos, "
                f"{len(all_segments)} segmentos, {elapsed_ms}ms"
            )
            # Log de estadísticas de caché
            stats = translation_cache.stats()
            logger.info(f"  Caché: {stats['hit_rate']} ({stats['hits']} hits, {stats['misses']} misses)")
        
        # Determinar idiomas según dirección
        if request.direction == "es-da":
            source_lang, target_lang = "spa_Latn", "dan_Latn"
        else:  # da-es
            source_lang, target_lang = "dan_Latn", "spa_Latn"
        
        # Construir respuesta
        response = TranslateResponse(
            provider="nllb-ct2-int8",
            direction=request.direction,
            source=source_lang,
            target=target_lang,
            translations=translations
        )
        
        return response
        
    except HTTPException:
        raise
    except ValueError as e:
        # Error de validación (no latino)
        logger.error(f"Validación falló: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"No se pudo asegurar salida en danés: {str(e)}"
        )
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
    import time
    start_time = time.time()
    
    # Verificar que el modelo esté cargado
    if not model_manager.model_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "El modelo está cargando o no está disponible. "
                "Espera unos segundos y reintenta. "
                "Consulta /health para diagnóstico detallado."
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
        
        # Extraer bloques HTML y textos
        blocks, texts_to_translate = split_html_preserving_structure(html_clean)
        
        if not texts_to_translate:
            # HTML sin texto traducible
            return TranslateHTMLResponse(
                provider="nllb-ct2-int8",
                source="spa_Latn",
                target="dan_Latn",
                html=html_clean
            )
        
        # Aplicar glosario pre-traducción si existe
        if request.glossary:
            texts_to_translate = [
                apply_glossary_pre(t, request.glossary)
                for t in texts_to_translate
            ]
        
        # Resolver max_new_tokens: usar cálculo adaptativo si no se especifica
        resolved_max_new_tokens = resolve_max_new_tokens(
            request.max_new_tokens, 
            texts_to_translate
        )
        
        # Traducir con caché, post-procesado y dirección
        translated_texts = translate_batch(
            texts_to_translate,
            direction=request.direction,
            max_new_tokens=resolved_max_new_tokens,
            use_cache=True,
            formal=request.formal or settings.FORMAL_DA,
            strict_max=request.strict_max
        )
        
        # Aplicar glosario post-traducción si existe
        if request.glossary:
            translated_texts = [
                apply_glossary_post(t, request.glossary)
                for t in translated_texts
            ]
        
        # Reconstruir HTML
        html_translated = rehydrate_html(blocks, translated_texts)
        
        # Métricas finales
        elapsed_ms = int((time.time() - start_time) * 1000)
        
        if not settings.LOG_TRANSLATIONS:
            logger.info(f"✓ HTML traducido: {len(texts_to_translate)} bloques, {elapsed_ms}ms")
            stats = translation_cache.stats()
            logger.info(f"  Caché: {stats['hit_rate']} ({stats['hits']} hits)")
        
        # Determinar idiomas según dirección
        if request.direction == "es-da":
            source_lang, target_lang = "spa_Latn", "dan_Latn"
        else:  # da-es
            source_lang, target_lang = "dan_Latn", "spa_Latn"
        
        # Construir respuesta
        response = TranslateHTMLResponse(
            provider="nllb-ct2-int8",
            direction=request.direction,
            source=source_lang,
            target=target_lang,
            html=html_translated
        )
        
        return response
        
    except HTTPException:
        raise
    except ValueError as e:
        # Error de validación (no latino)
        logger.error(f"Validación HTML falló: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"No se pudo asegurar salida en danés: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error en traducción HTML: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al traducir HTML: {str(e)}"
        )


@app.get("/info")
async def info():
    """
    Devuelve información detallada del modelo y métricas agregadas del servidor.
    
    NO incluye contenido de usuario por privacidad.
    """
    health_info = model_manager.health()
    cache_stats = translation_cache.stats()
    
    # Calcular uptime
    uptime_delta = datetime.now() - SERVER_START_TIME
    uptime_str = str(uptime_delta).split('.')[0]  # Formato HH:MM:SS
    
    # Métricas de rendimiento (sin contenido de usuario)
    performance_metrics = {
        "avg_request_time_ms": getattr(translation_cache, 'avg_request_time', 0),
        "total_requests": getattr(translation_cache, 'total_requests', 0),
        "threads_config": {
            "ct2_inter_threads": settings.CT2_INTER_THREADS,
            "ct2_intra_threads": settings.CT2_INTRA_THREADS
        }
    }
    
    return {
        "version": VERSION,
        "uptime": uptime_str,
        "model": {
            "loaded": health_info["model_loaded"],
            "paths": health_info["paths"],
            "config": health_info["config"],
            "load_time_ms": health_info["load_time_ms"]
        },
        "performance": performance_metrics,
        "cache": cache_stats,
        "capabilities": {
            "supported_directions": ["es-da", "da-es"],
            "source_languages": ["spa_Latn", "dan_Latn"],
            "target_languages": ["dan_Latn", "spa_Latn"],
            "bidirectional": True,
            "supports_glossary": True,
            "supports_batch": True,
            "supports_html": True,
            "supports_cache": True,
            "supports_segmentation": True,
            "supports_formal_style": True,
            "supports_case_insensitive_glossary": True,
            "max_batch_size": settings.MAX_BATCH_SIZE,
            "max_tokens_per_translation": settings.MAX_MAX_NEW_TOKENS,
            "auto_tokens_enabled": True,
            "continuation_enabled": True
        },
        "limits": {
            "max_input_tokens": settings.MAX_INPUT_TOKENS,
            "default_max_new_tokens": settings.DEFAULT_MAX_NEW_TOKENS,
            "max_max_new_tokens": settings.MAX_MAX_NEW_TOKENS,
            "max_segment_chars": settings.MAX_SEGMENT_CHARS,
            "request_timeout": settings.REQUEST_TIMEOUT
        }
    }


@app.post("/cache/clear")
async def clear_cache():
    """Limpia el caché de traducciones."""
    stats_before = translation_cache.stats()
    translation_cache.clear()
    
    return {
        "message": "Caché limpiado exitosamente",
        "entries_cleared": stats_before["size"]
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

