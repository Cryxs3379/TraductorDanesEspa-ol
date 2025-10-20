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


def _derive_max_new_tokens(input_lengths: List[int]) -> int:
    """
    Calcula max_new_tokens adaptativo basado en la longitud de entrada.
    
    Heurística: salida ~ 1.2x del input más largo.
    
    Args:
        input_lengths: Lista de longitudes de input_ids
        
    Returns:
        max_new_tokens recomendado (entre 128 y MAX_MAX_NEW_TOKENS)
        
    Examples:
        >>> _derive_max_new_tokens([50, 100])
        128
        >>> _derive_max_new_tokens([400, 500])
        512
    """
    if not input_lengths:
        return settings.DEFAULT_MAX_NEW_TOKENS
    
    max_input_len = max(input_lengths)
    estimated = int(max_input_len * 1.2)  # ~20% más que el input más largo
    
    # Clamp entre 128 y MAX_MAX_NEW_TOKENS (512)
    return max(128, min(settings.MAX_MAX_NEW_TOKENS, estimated))


def _needs_continuation(tokens: List[str], max_tokens: int) -> bool:
    """
    Determina si una traducción necesita continuación automática.
    
    Criterios:
    - Tocó el techo de tokens (len >= max_tokens - 1)
    - No termina en puntuación de cierre (., !, ?, …)
    
    Args:
        tokens: Lista de tokens generados
        max_tokens: Límite máximo usado
        
    Returns:
        True si necesita continuación
    """
    if len(tokens) < max_tokens - 1:
        return False
    
    # Verificar si termina con puntuación de cierre
    last_token = tokens[-1] if tokens else ""
    ending_punctuation = ['.', '!', '?', '…', '。', '！', '？']
    
    return not any(last_token.endswith(punct) for punct in ending_punctuation)


def translate_batch(
    texts: List[str],
    direction: str = "es-da",
    max_new_tokens: Optional[int] = None,
    beam_size: Optional[int] = None,
    use_cache: bool = True,
    formal: bool = False,
    strict_max: bool = False
) -> List[str]:
    """
    Traduce un batch de textos entre español y danés (bidireccional).
    
    Incluye caché LRU, post-procesado, validación de salida y continuación automática.
    Soporta ES→DA y DA→ES.
    
    Args:
        texts: Lista de textos a traducir
        direction: Dirección de traducción ("es-da" o "da-es")
        max_new_tokens: Máximo número de tokens a generar (None = auto-calculado)
        beam_size: Tamaño del beam search (default: settings.BEAM_SIZE)
        use_cache: Si True, usa caché para evitar retraducciones
        formal: Si True, aplica estilo formal (solo para salida danesa)
        strict_max: Si True, NO elevar max_new_tokens ni hacer continuación automática
        
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
    
    # max_new_tokens se calculará después de tokenizar (necesitamos input_lengths)
    
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
        
        # Calcular/elevar max_new_tokens según lógica adaptativa + elevación server-side
        input_lengths = [len(ids) for ids in input_ids_list]
        derived = _derive_max_new_tokens(input_lengths)
        
        if max_new_tokens is None:
            # Cliente no especificó: usar derivado
            max_new_tokens = derived
            logger.debug(f"max_new_tokens auto-calculado: {max_new_tokens}")
        else:
            # Cliente especificó un valor
            if strict_max:
                # Respetar exactamente el valor del cliente
                logger.debug(f"max_new_tokens (strict): {max_new_tokens}")
            else:
                # Elevar al mínimo recomendado si es necesario
                original = max_new_tokens
                max_new_tokens = max(max_new_tokens, derived)
                if max_new_tokens != original:
                    logger.info(f"max_new_tokens elevado: {original} → {max_new_tokens} (recomendado)")
        
        # Clamp final al cap de seguridad
        max_new_tokens = min(max_new_tokens, settings.MAX_MAX_NEW_TOKENS)
        
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
        
        # Continuación automática si tocó el techo sin terminar correctamente
        if not strict_max and max_new_tokens < settings.MAX_MAX_NEW_TOKENS:
            continuation_indices = []
            for i, tokens in enumerate(hypotheses):
                if _needs_continuation(tokens, max_new_tokens):
                    continuation_indices.append(i)
            
            if continuation_indices:
                logger.info(f"Continuación automática para {len(continuation_indices)} item(s) truncado(s)")
                
                for idx in continuation_indices:
                    # Target prefix = tokens ya generados
                    prefix_tokens = hypotheses[idx]
                    new_max = min(max_new_tokens + settings.CONTINUATION_INCREMENT, settings.MAX_MAX_NEW_TOKENS)
                    
                    # Segunda pasada con los tokens previos como prefix
                    continuation_result = translator.translate_batch(
                        [source_tokens[idx]],
                        target_prefix=[[tgt_bos_tok] + prefix_tokens],  # incluir BOS + tokens previos
                        beam_size=beam_size,
                        max_decoding_length=new_max - len(prefix_tokens),  # solo generar lo que falta
                        return_scores=False,
                        repetition_penalty=1.2,
                        no_repeat_ngram_size=3
                    )
                    
                    # Obtener tokens de continuación
                    continuation_tokens = continuation_result[0].hypotheses[0]
                    
                    # Concatenar (evitar duplicar el primer token si el decoder lo repite)
                    if continuation_tokens and continuation_tokens[0] == prefix_tokens[-1]:
                        continuation_tokens = continuation_tokens[1:]
                    
                    hypotheses[idx] = prefix_tokens + continuation_tokens
                    logger.debug(f"Item {idx}: continuación agregó {len(continuation_tokens)} tokens")
        
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

