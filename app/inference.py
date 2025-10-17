"""
Motor de inferencia usando CTranslate2 para traducción NLLB.

Usa ModelManager para acceso al modelo y garantiza traducción determinística ES→DA.
"""
import re
import logging
from typing import List

from app.settings import settings
from app.startup import model_manager


# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Nota: load_model() ahora está en ModelManager (app/startup.py)


def translate_batch(
    texts: List[str],
    max_new_tokens: int = 256,
    beam_size: int = None
) -> List[str]:
    """
    Traduce un batch de textos de español a danés.
    
    Garantiza que la salida sea en alfabeto latino (danés).
    Si detecta caracteres no latinos, reintenta con beam_size mayor.
    
    Args:
        texts: Lista de textos en español
        max_new_tokens: Máximo número de tokens a generar
        beam_size: Tamaño del beam search (default: usa settings.BEAM_SIZE)
        
    Returns:
        Lista de traducciones en danés
        
    Raises:
        RuntimeError: Si el modelo no está cargado
        Exception: Si hay error en la traducción
    """
    # Acceder al modelo via ModelManager
    if not model_manager.model_loaded:
        raise RuntimeError(
            "Modelo no cargado. El servidor arrancó pero el modelo no está disponible. "
            "Revisa /health para diagnóstico."
        )
    
    translator = model_manager.translator
    tokenizer = model_manager.tokenizer
    tgt_bos_tok = model_manager.tgt_bos_tok
    
    if not texts:
        return []
    
    # Usar beam_size por defecto de settings si no se especifica
    if beam_size is None:
        beam_size = settings.BEAM_SIZE
    
    try:
        # Pre-procesar textos: normalizar espacios
        texts_normalized = [_normalize_text(text) for text in texts]
        
        # Tokenizar textos de entrada SIN TORCH (solo listas de IDs)
        # NLLB espera source language token al inicio
        # El tokenizador ya añade este token automáticamente si src_lang está configurado
        encoded = tokenizer(
            texts_normalized,
            padding=True,
            truncation=True,
            max_length=384,  # Más corto para mejor rendimiento
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
        
        # Preparar target_prefix con token de idioma destino (DANÉS)
        # NLLB requiere el token del idioma destino al inicio de la generación
        if not tgt_bos_tok:
            raise RuntimeError(
                "Token de idioma danés no configurado. "
                "Verifica que el modelo NLLB esté correctamente cargado."
            )
        
        target_prefix = [[tgt_bos_tok]] * len(texts)
        
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
        
        # Convertir tokens a texto
        translations = []
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
                    f"Salida con caracteres no latinos detectada (texto {i+1}). "
                    f"Reintentando con beam_size={beam_size + 1}..."
                )
                # Reintentar este texto específico con beam_size mayor
                if beam_size < 8:  # Límite de reintentos
                    retry_result = translate_batch(
                        [texts[i]], 
                        max_new_tokens=max_new_tokens, 
                        beam_size=beam_size + 1
                    )
                    text = retry_result[0]
                else:
                    logger.error(
                        f"No se pudo obtener salida en alfabeto latino después de varios intentos. "
                        f"Texto: {texts[i][:50]}..."
                    )
            
            translations.append(text)
        
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

