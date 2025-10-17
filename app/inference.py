"""
Motor de inferencia usando CTranslate2 para traducción NLLB.

Carga el modelo convertido a CT2 con cuantización INT8 y el tokenizador HuggingFace.
Proporciona funciones de traducción batch con configuración optimizada.
"""
import os
import logging
from typing import List, Optional

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
        logger.info("✓ Tokenizador HuggingFace cargado")
        
        # Obtener token de idioma destino para NLLB
        if hasattr(tokenizer, 'lang_code_to_id'):
            target_lang_id = tokenizer.lang_code_to_id.get(TARGET_LANG)
            if target_lang_id is not None:
                target_lang_token = tokenizer.convert_ids_to_tokens(target_lang_id)
                logger.info(f"✓ Token de idioma destino: {target_lang_token} (ID: {target_lang_id})")
            else:
                logger.warning(f"No se encontró ID para idioma {TARGET_LANG}")
        else:
            logger.warning("El tokenizador no tiene lang_code_to_id")
        
        # Warmup: traducción de prueba
        logger.info("Ejecutando warmup...")
        try:
            warmup_text = ["Hola"]
            _ = translate_batch(warmup_text, max_new_tokens=10)
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
    beam_size: int = 4
) -> List[str]:
    """
    Traduce un batch de textos de español a danés.
    
    Args:
        texts: Lista de textos en español
        max_new_tokens: Máximo número de tokens a generar
        beam_size: Tamaño del beam search
        
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
    
    try:
        # Tokenizar textos de entrada
        # NLLB espera source language token al inicio
        # El tokenizador ya añade este token automáticamente
        encoded = tokenizer(
            texts,
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
        
        # Traducir con CTranslate2
        results = translator.translate_batch(
            source_tokens,
            target_prefix=target_prefix,
            beam_size=beam_size,
            max_decoding_length=max_new_tokens,
            return_scores=False
        )
        
        # Extraer hipótesis (primera de cada beam)
        hypotheses = [result.hypotheses[0] for result in results]
        
        # Convertir tokens a texto
        translations = []
        for tokens in hypotheses:
            # Convertir tokens a IDs
            token_ids = tokenizer.convert_tokens_to_ids(tokens)
            
            # Decodificar a texto
            text = tokenizer.decode(
                token_ids,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=True
            )
            
            translations.append(text)
        
        return translations
        
    except Exception as e:
        logger.error(f"Error en traducción: {e}")
        raise Exception(f"Error al traducir: {str(e)}")


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
        "intra_threads": CT2_INTRA_THREADS
    }

