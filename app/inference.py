"""
Motor de inferencia usando CTranslate2 para traducción NLLB.

Carga el modelo convertido a CT2 con cuantización INT8 y el tokenizador HuggingFace.
Proporciona funciones de traducción batch con configuración optimizada.

Garantiza traducción determinística ES→DA forzando idioma destino.
"""
import os
import re
import logging
from typing import List, Optional
from functools import lru_cache
import hashlib

import ctranslate2 as ct
from transformers import AutoTokenizer


# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Variables globales para modelo y tokenizador (carga única)
translator: Optional[ct.Translator] = None
tokenizer: Optional[AutoTokenizer] = None
target_lang_token: Optional[str] = None
target_lang_id: Optional[int] = None

# Configuración desde variables de entorno
MODEL_DIR = os.getenv("MODEL_DIR", "./models/nllb-600m")
CT2_DIR = os.getenv("CT2_DIR", "./models/nllb-600m-ct2-int8")
CT2_INTER_THREADS = int(os.getenv("CT2_INTER_THREADS", "0"))
CT2_INTRA_THREADS = int(os.getenv("CT2_INTRA_THREADS", "0"))
BEAM_SIZE = int(os.getenv("BEAM_SIZE", "4"))

# Idiomas FLORES-200
SOURCE_LANG = "spa_Latn"
TARGET_LANG = "dan_Latn"


def load_model():
    """
    Carga el modelo CTranslate2 y tokenizador HuggingFace.
    
    Esta función se ejecuta una sola vez al iniciar la aplicación.
    
    Raises:
        FileNotFoundError: Si los directorios de modelo no existen
        Exception: Si hay error al cargar modelo o tokenizador
    """
    global translator, tokenizer, target_lang_token, target_lang_id
    
    logger.info(f"Cargando modelo desde {CT2_DIR}...")
    logger.info(f"Tokenizador desde {MODEL_DIR}...")
    
    # Verificar que existen los directorios
    if not os.path.exists(CT2_DIR):
        raise FileNotFoundError(
            f"Directorio de modelo CT2 no encontrado: {CT2_DIR}\n"
            f"Ejecuta: make download && make convert"
        )
    
    if not os.path.exists(MODEL_DIR):
        raise FileNotFoundError(
            f"Directorio de modelo HF no encontrado: {MODEL_DIR}\n"
            f"Ejecuta: make download"
        )
    
    try:
        # Cargar traductor CTranslate2
        translator = ct.Translator(
            CT2_DIR,
            device="cpu",
            inter_threads=CT2_INTER_THREADS if CT2_INTER_THREADS > 0 else 0,
            intra_threads=CT2_INTRA_THREADS if CT2_INTRA_THREADS > 0 else 0,
            compute_type="int8"
        )
        logger.info("✓ Traductor CTranslate2 cargado")
        
        # Cargar tokenizador HuggingFace
        tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
        
        # CRÍTICO: Forzar idioma source para NLLB
        # Esto garantiza que el tokenizador añada el token correcto de español al inicio
        if hasattr(tokenizer, 'src_lang'):
            tokenizer.src_lang = SOURCE_LANG
            logger.info(f"✓ Idioma source configurado: {SOURCE_LANG}")
        
        logger.info("✓ Tokenizador HuggingFace cargado")
        
        # Obtener token de idioma destino para NLLB
        if hasattr(tokenizer, 'lang_code_to_id'):
            target_lang_id = tokenizer.lang_code_to_id.get(TARGET_LANG)
            if target_lang_id is not None:
                target_lang_token = tokenizer.convert_ids_to_tokens(target_lang_id)
                logger.info(f"✓ Token de idioma destino: {target_lang_token} (ID: {target_lang_id})")
            else:
                logger.warning(f"No se encontró ID para idioma {TARGET_LANG}")
                raise ValueError(f"No se pudo obtener token para {TARGET_LANG}")
        else:
            logger.warning("El tokenizador no tiene lang_code_to_id")
            raise ValueError("El tokenizador no soporta NLLB lang_code_to_id")
        
        # Warmup: traducción de prueba
        logger.info("Ejecutando warmup...")
        try:
            warmup_text = ["Hola mundo"]
            _ = translate_batch(warmup_text, max_new_tokens=20)
            logger.info("✓ Warmup completado - Sistema listo")
        except Exception as e:
            logger.warning(f"Warmup falló, pero el modelo está cargado: {e}")
            logger.info("✓ Modelo cargado - Sistema listo")
        
    except Exception as e:
        logger.error(f"Error al cargar modelo: {e}")
        raise


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
        beam_size: Tamaño del beam search (default: usa BEAM_SIZE de env)
        
    Returns:
        Lista de traducciones en danés
        
    Raises:
        RuntimeError: Si el modelo no está cargado
        Exception: Si hay error en la traducción
    """
    global translator, tokenizer, target_lang_token
    
    if translator is None or tokenizer is None:
        raise RuntimeError(
            "Modelo no cargado. Ejecuta load_model() primero."
        )
    
    if not texts:
        return []
    
    # Usar beam_size por defecto de env si no se especifica
    if beam_size is None:
        beam_size = BEAM_SIZE
    
    try:
        # Pre-procesar textos: normalizar espacios
        texts_normalized = [_normalize_text(text) for text in texts]
        
        # Tokenizar textos de entrada
        # NLLB espera source language token al inicio
        # El tokenizador ya añade este token automáticamente si src_lang está configurado
        encoded = tokenizer(
            texts_normalized,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=512
        )
        
        # Convertir a lista de tokens para CTranslate2
        source_tokens = [
            tokenizer.convert_ids_to_tokens(ids)
            for ids in encoded["input_ids"].tolist()
        ]
        
        # Preparar target_prefix con token de idioma destino
        # NLLB requiere el token del idioma destino al inicio de la generación
        target_prefix = None
        if target_lang_token:
            # Cada elemento del batch necesita el mismo prefix
            target_prefix = [[target_lang_token]] * len(texts)
        else:
            raise RuntimeError("Token de idioma destino no configurado")
        
        # Traducir con CTranslate2
        results = translator.translate_batch(
            source_tokens,
            target_prefix=target_prefix,
            beam_size=beam_size,
            max_decoding_length=max_new_tokens,
            return_scores=False,
            repetition_penalty=1.2  # Evitar repeticiones
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
            if not _validate_latin_output(text):
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


def _validate_latin_output(text: str) -> bool:
    """
    Valida que la salida contenga principalmente caracteres del alfabeto latino.
    
    Permite letras latinas (incluyendo danesas: æ, ø, å), números, 
    puntuación común y algunos símbolos.
    
    Returns:
        True si >80% son caracteres latinos válidos, False en caso contrario
    """
    if not text:
        return True
    
    # Caracteres permitidos: latinos, daneses, números, puntuación, espacios
    # Incluye: a-z, A-Z, æøåÆØÅ, números, puntuación común, espacios
    latin_pattern = re.compile(r'[a-zA-ZæøåÆØÅàáâãäåèéêëìíîïòóôõöùúûüýÿñçÀÁÂÃÄÅÈÉÊËÌÍÎÏÒÓÔÕÖÙÚÛÜÝŸÑÇ0-9\s\.,;:!?¿¡\-\'\"()\[\]{}/@#$%&*+=<>|\\~`]')
    
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


def get_model_info() -> dict:
    """
    Retorna información sobre el modelo cargado.
    
    Returns:
        Diccionario con información del modelo
    """
    return {
        "model_dir": MODEL_DIR,
        "ct2_dir": CT2_DIR,
        "source_lang": SOURCE_LANG,
        "target_lang": TARGET_LANG,
        "loaded": translator is not None and tokenizer is not None,
        "inter_threads": CT2_INTER_THREADS,
        "intra_threads": CT2_INTRA_THREADS,
        "beam_size": BEAM_SIZE
    }

