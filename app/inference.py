"""
Motor de inferencia usando CTranslate2 para traducción NLLB.

Usa ModelManager para acceso al modelo y garantiza traducción determinística ES→DA.
Incluye caché LRU para evitar retraducciones.
"""
import re
import logging
from typing import List, Optional

from app.settings import settings
from app.startup import model_manager
from app.cache import translation_cache
from app.postprocess_da import postprocess_da
from app.postprocess_es import postprocess_es


# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Nota: load_model() ahora está en ModelManager (app/startup.py)


def translate_batch(
    texts: List[str],
    direction: str = "es-da",
    max_new_tokens: int = None,
    beam_size: int = None,
    use_cache: bool = True,
    formal: bool = False
) -> List[str]:
    """
    Traduce un batch de textos entre español y danés (bidireccional).
    
    Incluye caché LRU, post-procesado y validación de salida.
    Soporta ES→DA y DA→ES.
    
    Args:
        texts: Lista de textos a traducir
        direction: Dirección de traducción ("es-da" o "da-es")
        max_new_tokens: Máximo número de tokens a generar (default: settings.MAX_NEW_TOKENS)
        beam_size: Tamaño del beam search (default: settings.BEAM_SIZE)
        use_cache: Si True, usa caché para evitar retraducciones
        formal: Si True, aplica estilo formal (solo para salida danesa)
        
    Returns:
        Lista de traducciones post-procesadas
        
    Raises:
        RuntimeError: Si el modelo no está cargado
        ValueError: Si direction es inválida
        Exception: Si hay error en la traducción
    """
    # Validar dirección
    if direction not in ["es-da", "da-es"]:
        raise ValueError(f"Dirección inválida: {direction}. Usa 'es-da' o 'da-es'")
    
    # Acceder al modelo via ModelManager
    if not model_manager.model_loaded:
        raise RuntimeError(
            "Modelo no cargado. El servidor arrancó pero el modelo no está disponible. "
            "Revisa /health para diagnóstico."
        )
    
    translator = model_manager.translator
    tokenizer = model_manager.tokenizer
    
    if not texts:
        return []
    
    # Usar defaults de settings si no se especifican
    if beam_size is None:
        beam_size = settings.BEAM_SIZE
    if max_new_tokens is None:
        max_new_tokens = settings.MAX_NEW_TOKENS
    
    # Configurar idiomas según dirección
    if direction == "es-da":
        src_lang = "spa_Latn"
        tgt_lang = "dan_Latn"
    else:  # da-es
        src_lang = "dan_Latn"
        tgt_lang = "spa_Latn"
    
    # Obtener token BOS del idioma target
    if not hasattr(tokenizer, 'lang_code_to_id'):
        raise RuntimeError("Tokenizador no soporta lang_code_to_id (no es NLLB)")
    
    tgt_lang_id = tokenizer.lang_code_to_id.get(tgt_lang)
    if tgt_lang_id is None:
        raise RuntimeError(f"No se encontró token para idioma {tgt_lang}")
    
    tgt_bos_tok = tokenizer.convert_ids_to_tokens(tgt_lang_id)
    
    # Separar textos en caché vs no caché (con dirección)
    translations = [None] * len(texts)
    texts_to_translate = []
    indices_to_translate = []
    
    if use_cache:
        for i, text in enumerate(texts):
            # Incluir dirección en la clave del caché
            cache_key = f"{direction}||{text}"
            cached = translation_cache.get(cache_key)
            if cached is not None:
                translations[i] = cached
            else:
                texts_to_translate.append(text)
                indices_to_translate.append(i)
    else:
        texts_to_translate = texts
        indices_to_translate = list(range(len(texts)))
    
    # Si no hay nada que traducir (todo en caché), retornar
    if not texts_to_translate:
        logger.info(f"Cache: 100% hits ({len(texts)} textos)")
        return translations
    
    if use_cache:
        logger.info(f"Cache: {len(translations) - len(texts_to_translate)} hits, {len(texts_to_translate)} misses")
    
    try:
        # Pre-procesar textos: normalizar espacios
        texts_normalized = [_normalize_text(text) for text in texts_to_translate]
        
        # Configurar idioma source en el tokenizador
        if hasattr(tokenizer, 'src_lang'):
            tokenizer.src_lang = src_lang
            logger.debug(f"Idioma source configurado: {src_lang}")
        
        # Tokenizar textos de entrada SIN TORCH (solo listas de IDs)
        # NLLB espera source language token al inicio
        # El tokenizador ya añade este token automáticamente si src_lang está configurado
        encoded = tokenizer(
            texts_normalized,
            padding=True,
            truncation=True,
            max_length=settings.MAX_INPUT_TOKENS if hasattr(settings, 'MAX_INPUT_TOKENS') else 384,
            return_attention_mask=False,
            return_token_type_ids=False
        )
        
        # input_ids ya es una lista de listas (sin tensores)
        input_ids_list = encoded["input_ids"]
        
        # Convertir IDs a tokens para CTranslate2
        source_tokens = [
            tokenizer.convert_ids_to_tokens(ids)
            for ids in input_ids_list
        ]
        
        # Preparar target_prefix con token de idioma destino
        # NLLB requiere el token del idioma destino al inicio de la generación
        if not tgt_bos_tok:
            raise RuntimeError(
                f"Token de idioma {tgt_lang} no configurado. "
                "Verifica que el modelo NLLB esté correctamente cargado."
            )
        
        target_prefix = [[tgt_bos_tok]] * len(texts_to_translate)
        
        # Traducir con CTranslate2 (parámetros conservadores para evitar cuelgues)
        results = translator.translate_batch(
            source_tokens,
            target_prefix=target_prefix,
            beam_size=beam_size,
            max_decoding_length=max_new_tokens,
            return_scores=False,
            repetition_penalty=1.2,  # Evitar repeticiones
            no_repeat_ngram_size=3   # Evitar repetición de 3-gramas
        )
        
        # Extraer hipótesis (primera de cada beam)
        hypotheses = [result.hypotheses[0] for result in results]
        
        # Convertir tokens a texto y post-procesar
        new_translations = []
        for i, tokens in enumerate(hypotheses):
            # Convertir tokens a IDs
            token_ids = tokenizer.convert_tokens_to_ids(tokens)
            
            # Decodificar a texto
            text = tokenizer.decode(
                token_ids,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=True
            )
            
            # Post-procesamiento: limpiar artefactos
            text = _clean_translation(text)
            
            # Validación: verificar que la salida es alfabeto latino
            if not is_mostly_latin(text):
                logger.warning(
                    f"Salida con caracteres no latinos detectada (segmento {i+1}). "
                    f"Reintentando con beam_size={min(beam_size + 1, 5)}..."
                )
                # Reintentar UNA VEZ con beam_size mayor
                if beam_size < 5:
                    retry_result = translate_batch(
                        [texts_to_translate[i]], 
                        max_new_tokens=max_new_tokens, 
                        beam_size=min(beam_size + 1, 5),
                        use_cache=False,  # No usar caché en reintentos
                        formal=formal
                    )
                    text = retry_result[0]
                else:
                    # Error controlado si persiste
                    raise ValueError(
                        f"No se pudo obtener salida en alfabeto latino. "
                        f"Texto original: {texts_to_translate[i][:100]}..."
                    )
            
            # Post-procesado según idioma destino
            if direction == "es-da":
                text = postprocess_da(text, formal=formal)
            else:  # da-es
                text = postprocess_es(text)
            
            new_translations.append(text)
            
            # Guardar en caché (con dirección)
            if use_cache:
                cache_key = f"{direction}||{texts_to_translate[i]}"
                translation_cache.put(cache_key, text)
        
        # Insertar traducciones nuevas en las posiciones correctas
        for i, idx in enumerate(indices_to_translate):
            translations[idx] = new_translations[i]
        
        return translations
        
    except Exception as e:
        logger.error(f"Error en traducción: {e}", exc_info=True)
        raise Exception(f"Error al traducir: {str(e)}")


def _normalize_text(text: str) -> str:
    """
    Normaliza el texto de entrada: espacios, saltos de línea, etc.
    
    Preserva URLs, emails y números.
    """
    # Normalizar espacios múltiples
    text = re.sub(r'\s+', ' ', text)
    # Eliminar espacios al inicio y final
    text = text.strip()
    return text


def _clean_translation(text: str) -> str:
    """
    Limpia artefactos en la traducción generada.
    
    - Elimina tokens de idioma visibles si aparecen (ej: "dan_Latn")
    - Normaliza espacios
    """
    # Eliminar posibles tokens de idioma que se hayan colado
    text = re.sub(r'\b(dan_Latn|spa_Latn)\b', '', text)
    
    # Eliminar marcadores residuales BOS/EOS si aparecen como texto
    text = re.sub(r'<\|.*?\|>', '', text)
    
    # Normalizar espacios múltiples resultantes
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text


def is_mostly_latin(text: str) -> bool:
    """
    Valida que el texto contenga principalmente caracteres del alfabeto latino.
    
    Permite letras latinas (incluyendo danesas: æ, ø, å), números, 
    puntuación común y algunos símbolos.
    
    Args:
        text: Texto a validar
    
    Returns:
        True si >80% son caracteres latinos válidos, False en caso contrario
    """
    if not text:
        return True
    
    # Caracteres permitidos: latinos, daneses, números, puntuación, espacios
    # Incluye: a-z, A-Z, æøåÆØÅ, números, puntuación común, espacios
    latin_pattern = re.compile(
        r'[a-zA-ZæøåÆØÅàáâãäåèéêëìíîïòóôõöùúûüýÿñçÀÁÂÃÄÅÈÉÊËÌÍÎÏÒÓÔÕÖÙÚÛÜÝŸÑÇ0-9\s\.,;:!?¿¡\-\'\"()\[\]{}/@#$%&*+=<>|\\~`]'
    )
    
    # Contar caracteres latinos vs total
    latin_chars = len(latin_pattern.findall(text))
    total_chars = len(text)
    
    if total_chars == 0:
        return True
    
    ratio = latin_chars / total_chars
    
    # Si más del 20% son caracteres no latinos, considerar inválido
    if ratio < 0.8:
        logger.warning(
            f"Texto con baja proporción de caracteres latinos: {ratio:.2%}. "
            f"Muestra: {text[:100]}"
        )
        return False
    
    return True


# Nota: get_model_info() ahora está en ModelManager.health() (app/startup.py)

