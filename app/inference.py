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
from app.utils_text import (
    normalize_preserving_newlines,
    translate_preserving_structure
)


# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Nota: load_model() ahora está en ModelManager (app/startup.py)


def _derive_max_new_tokens(input_lengths: List[int]) -> int:
    """
    Calcula max_new_tokens generosamente para evitar truncado.
    
    NUEVA LÓGICA: Siempre generar valores muy altos para asegurar traducción completa.
    
    Args:
        input_lengths: Lista de longitudes de input_ids
        
    Returns:
        max_new_tokens muy generoso (sin límites artificiales)
    """
    if not input_lengths:
        # Valor por defecto muy alto si no hay input
        return 4096
    
    max_input_len = max(input_lengths)
    
    # LÓGICA MUY GENEROSA: factor mínimo 3.0x y hasta 5.0x para textos largos
    if max_input_len <= 100:
        factor = 3.0  # Muy generoso incluso para textos cortos
    elif max_input_len <= 300:
        factor = 4.0  # Extremadamente generoso
    else:
        factor = 5.0  # Máximo generoso para textos largos
    
    estimated = int(max_input_len * factor)
    
    # Mínimo absoluto de 1024 tokens, sin máximo
    return max(1024, estimated)


def _needs_continuation(tokens: List[str], max_tokens: int) -> bool:
    """
    Determina si una traducción necesita continuación automática.
    
    LÓGICA EXTREMADAMENTE AGRESIVA:
    - Detectar cualquier indicio de truncado posible
    
    Args:
        tokens: Lista de tokens generados
        max_tokens: Límite máximo usado
        
    Returns:
        True si necesita continuación
    """
    if not tokens:
        return False
    
    logger.info(f"Evaluando continuación: {len(tokens)}/{max_tokens} tokens")
    
    # CRITERIO 1: Longitud mínima absoluta para textos largos
    # Si tenemos muchos tokens pero no terminamos bien, continuar
    if len(tokens) > 200:  # Para textos largos, ser más estricto
        last_token = tokens[-1] if tokens else ""
        ending_punctuation = ['.', '!', '?', '…', '。', '！', '？', ')', '"', "'"]
        ends_properly = any(last_token.endswith(punct) for punct in ending_punctuation)
        
        if not ends_properly:
            logger.info(f"CRITERIO 1 - Necesita continuación: texto largo sin fin apropiado: '{last_token}'")
            return True
    
    # CRITERIO 2: Threshold bajo para cualquier caso
    threshold = int(max_tokens * 0.3)  # Muy bajo: 30%
    if len(tokens) >= threshold:
        last_token = tokens[-1] if tokens else ""
        ending_punctuation = ['.', '!', '?', '…', '。', '！', '？', ')', '"', "'"]
        ends_properly = any(last_token.endswith(punct) for punct in ending_punctuation)
        
        if not ends_properly:
            logger.info(f"CRITERIO 2 - Necesita continuación: threshold bajo sin fin apropiado: {len(tokens)}/{max_tokens}")
            return True
    
    # CRITERIO 3: Para textos de longitud media, verificar finalización natural
    if len(tokens) > 100:
        # Concatenar últimos tokens para verificar patrón
        last_tokens_text = " ".join(tokens[-5:]).lower()
        
        # Detectar si parece incompleto
        incomplete_patterns = ["fordi", "så", "desuden", "derfor", "men", "og"]
        if any(pattern in last_tokens_text for pattern in incomplete_patterns):
            logger.info(f"CRITERIO 3 - Necesita continuación: patrón incompleto detectado")
            return True
    
    logger.info(f"No necesita continuación")
    return False


def translate_batch(
    texts: List[str],
    direction: str = "es-da",
    max_new_tokens: Optional[int] = None,
    beam_size: Optional[int] = None,
    use_cache: bool = True,
    formal: bool = False,
    strict_max: bool = False,
    preserve_newlines: bool = True
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
        preserve_newlines: Si True, preserva todos los saltos de línea del original
        
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
        texts_normalized = [
            _normalize_text(text, preserve_newlines=preserve_newlines) 
            for text in texts_to_translate
        ]
        
        # Configurar idioma source en el tokenizador
        if hasattr(tokenizer, 'src_lang'):
            tokenizer.src_lang = src_lang
            logger.debug(f"Idioma source configurado: {src_lang}")
        
        # Tokenizar textos de entrada SIN TORCH (solo listas de IDs)
        # NLLB espera source language token al inicio
        # El tokenizador ya añade este token automáticamente si src_lang está configurado
        # Usar límite muy alto para evitar truncado de entrada
        safe_input_limit = max(8192, settings.MAX_INPUT_TOKENS)
        logger.info(f"🔧 Tokenizando con límite de entrada: {safe_input_limit}")
        
        encoded = tokenizer(
            texts_normalized,
            padding=True,
            truncation=True,  # Mantener pero con límite muy alto
            max_length=safe_input_limit,
            return_attention_mask=False,
            return_token_type_ids=False
        )
        
        # input_ids ya es una lista de listas (sin tensores)
        input_ids_list = encoded["input_ids"]
        
        # Calcular/elevar max_new_tokens según lógica adaptativa + elevación server-side
        input_lengths = [len(ids) for ids in input_ids_list]
        derived = _derive_max_new_tokens(input_lengths)
        
        # Debug logging mejorado para investigar truncado
        logger.info(f"🔍 INFERENCE DEBUG - max_new_tokens recibido: {max_new_tokens}")
        logger.info(f"🔍 INFERENCE DEBUG - input_lengths: {input_lengths}")
        logger.info(f"🔍 INFERENCE DEBUG - derived: {derived}")
        logger.info(f"🔍 INFERENCE DEBUG - strict_max: {strict_max}")
        
        if max_new_tokens is None:
            # Cliente no especificó: usar valor extremadamente alto para evitar truncado
            max_new_tokens = max(4096, derived)  # Mínimo 4096 tokens
            logger.info(f"🔄 max_new_tokens auto-calculado (EXTREMO): {max_new_tokens}")
        else:
            # Cliente especificó un valor
            if strict_max:
                # Respetar exactamente el valor del cliente
                logger.info(f"🔒 max_new_tokens (strict): {max_new_tokens}")
            else:
                # SIEMPRE elevar a valores extremadamente altos para evitar truncado
                original = max_new_tokens
                max_new_tokens = max(max_new_tokens, max(4096, derived))  # Mínimo 4096 siempre
                if max_new_tokens != original:
                    logger.info(f"📈 max_new_tokens elevado automáticamente: {original} → {max_new_tokens} (extremo)")
        
        # NO aplicar límites artificiales - permitir traducción completa
        # max_new_tokens ya está calculado correctamente arriba
        
        logger.info(f"🚀 FINAL - Usando max_new_tokens: {max_new_tokens}")
        
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
        
        # Traducir con CTranslate2 usando valores muy altos para evitar truncado
        # Asegurar que nunca se limita artificialmente
        safe_max_tokens = max(8192, max_new_tokens)  # Mínimo 8192 tokens
        logger.info(f"🔧 Usando max_decoding_length: {safe_max_tokens}")
        
        results = translator.translate_batch(
            source_tokens,
            target_prefix=target_prefix,
            beam_size=beam_size,
            max_decoding_length=safe_max_tokens,
            return_scores=False,
            repetition_penalty=1.2,  # Evitar repeticiones
            no_repeat_ngram_size=3   # Evitar repetición de 3-gramas
        )
        
        # Extraer hipótesis (primera de cada beam)
        hypotheses = [result.hypotheses[0] for result in results]
        
        # Continuación automática SIEMPRE para textos largos (sin límites)
        if not strict_max:
            continuation_indices = []
            for i, tokens in enumerate(hypotheses):
                # LÓGICA SIMPLE: Si el texto original era largo, hacer continuación SIEMPRE
                original_text = texts_to_translate[i] if i < len(texts_to_translate) else ""
                is_long_text = len(original_text) > 500  # Texto de más de 500 chars
                
                if is_long_text or _needs_continuation(tokens, safe_max_tokens):
                    continuation_indices.append(i)
                    logger.info(f"Item {i}: candidato para continuación (long_text={is_long_text}, needs_cont={_needs_continuation(tokens, safe_max_tokens)})")
            
            if continuation_indices:
                logger.info(f"🔄 Continuación automática para {len(continuation_indices)} item(s)")
                
                for idx in continuation_indices:
                    # Target prefix = tokens ya generados
                    prefix_tokens = hypotheses[idx]
                    logger.info(f"Continuando item {idx}: tokens actuales={len(prefix_tokens)}")
                    
                    # EXTREMADAMENTE generoso para continuación - sin límites artificiales
                    new_max = 16384  # Valor fijo muy alto
                    
                    # Segunda pasada con los tokens previos como prefix
                    continuation_result = translator.translate_batch(
                        [source_tokens[idx]],
                        target_prefix=[[tgt_bos_tok] + prefix_tokens],  # incluir BOS + tokens previos
                        beam_size=beam_size,
                        max_decoding_length=new_max,  # Sin restar - usar valor alto completo
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
                    logger.info(f"Item {idx}: continuación agregó {len(continuation_tokens)} tokens. Total: {len(hypotheses[idx])}")
        
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


def _normalize_text(text: str, preserve_newlines: bool = True) -> str:
    """
    Normaliza el texto de entrada.
    
    Args:
        text: Texto a normalizar
        preserve_newlines: Si True, preserva TODOS los saltos de línea.
                          Si False, usa normalización legacy (limita a 2 saltos)
    
    Returns:
        Texto normalizado
    """
    if preserve_newlines:
        # Usar nueva lógica que preserva TODA la estructura
        return normalize_preserving_newlines(text)
    else:
        # Lógica legacy: normalizar espacios y limitar saltos de línea
        # Normalizar espacios múltiples PERO preservar saltos de línea
        text = re.sub(r'[ \t]+', ' ', text)  # Solo espacios y tabs, no \n
        # Normalizar saltos de línea múltiples a máximo 2 consecutivos
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Eliminar espacios al inicio y final de líneas
        lines = text.split('\n')
        lines = [line.strip() for line in lines]
        text = '\n'.join(lines)
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


def translate_text_preserving_structure(
    text: str,
    direction: str = "es-da",
    max_new_tokens: Optional[int] = None,
    formal: bool = False,
    strict_max: bool = False
) -> str:
    """
    Traduce un texto preservando TODA su estructura de saltos de línea.
    
    Divide el texto por bloques de párrafos (separados por \\n\\n+) y traduce
    cada bloque independientemente, luego reensambla usando los separadores originales.
    
    Args:
        text: Texto a traducir
        direction: Dirección de traducción ("es-da" o "da-es")
        max_new_tokens: Máximo de tokens por bloque (None = auto)
        formal: Aplicar estilo formal
        strict_max: No elevar max_new_tokens automáticamente
        
    Returns:
        Texto traducido con estructura preservada
    """
    def translate_block(block: str) -> str:
        """Función interna para traducir un bloque individual."""
        result = translate_batch(
            [block],
            direction=direction,
            max_new_tokens=max_new_tokens,
            use_cache=True,
            formal=formal,
            strict_max=strict_max,
            preserve_newlines=True
        )
        return result[0] if result else block
    
    # Usar utilidad de preservación de estructura
    return translate_preserving_structure(text, translate_block)


# Nota: get_model_info() ahora está en ModelManager.health() (app/startup.py)

