"""
Gestor de arranque y carga de modelo (singleton).

Separa la carga del modelo del arranque del servidor para garantizar
que la API siempre esté disponible, incluso si el modelo no se ha descargado aún.
"""
import os
import logging
import traceback
from pathlib import Path
from typing import Optional
from datetime import datetime

import ctranslate2 as ct
from transformers import AutoTokenizer

from app.settings import settings


logger = logging.getLogger(__name__)


class ModelManager:
    """
    Singleton que gestiona la carga y estado del modelo NLLB.
    
    Garantiza que el servidor pueda arrancar incluso si el modelo no está disponible,
    proporcionando información de estado a través de /health.
    """
    
    _instance: Optional['ModelManager'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Inicializa el manager (solo una vez por singleton)."""
        if self._initialized:
            return
            
        self.translator: Optional[ct.Translator] = None
        self.tokenizer: Optional[AutoTokenizer] = None
        self.tgt_bos_tok: Optional[str] = None
        self.tgt_lang_id: Optional[int] = None
        
        self.model_loaded: bool = False
        self.last_error: Optional[str] = None
        self.load_started_at: Optional[datetime] = None
        self.load_completed_at: Optional[datetime] = None
        
        self._initialized = True
    
    def probe_paths(self) -> dict:
        """
        Valida la existencia de los directorios y archivos clave del modelo.
        
        Returns:
            Dict con información de validación:
            {
                "model_dir_exists": bool,
                "ct2_dir_exists": bool,
                "model_files_ok": bool,
                "ct2_files_ok": bool,
                "missing_paths": list[str],
                "recommendations": list[str]
            }
        """
        model_dir = Path(settings.MODEL_DIR)
        ct2_dir = Path(settings.CT2_DIR)
        
        missing_paths = []
        recommendations = []
        
        # Verificar MODEL_DIR
        model_dir_exists = model_dir.exists()
        if not model_dir_exists:
            missing_paths.append(str(model_dir))
            recommendations.append(f"Ejecuta: make download")
        
        # Verificar archivos clave en MODEL_DIR
        model_files_ok = False
        if model_dir_exists:
            # Buscar config.json y al menos un archivo de pesos
            has_config = (model_dir / "config.json").exists()
            has_weights = (
                (model_dir / "pytorch_model.bin").exists() or
                (model_dir / "model.safetensors").exists()
            )
            model_files_ok = has_config and has_weights
            
            if not model_files_ok:
                missing_paths.append(f"{model_dir}/* (archivos incompletos)")
                recommendations.append("Modelo HuggingFace incompleto. Re-ejecuta: make download")
        
        # Verificar CT2_DIR
        ct2_dir_exists = ct2_dir.exists()
        if not ct2_dir_exists:
            missing_paths.append(str(ct2_dir))
            recommendations.append(f"Ejecuta: make convert")
        
        # Verificar archivos clave en CT2_DIR
        ct2_files_ok = False
        if ct2_dir_exists:
            has_model_bin = (ct2_dir / "model.bin").exists()
            has_config = (ct2_dir / "config.json").exists()
            ct2_files_ok = has_model_bin and has_config
            
            if not ct2_files_ok:
                missing_paths.append(f"{ct2_dir}/* (archivos incompletos)")
                recommendations.append("Modelo CTranslate2 incompleto. Re-ejecuta: make convert")
        
        result = {
            "model_dir_exists": model_dir_exists,
            "ct2_dir_exists": ct2_dir_exists,
            "model_files_ok": model_files_ok,
            "ct2_files_ok": ct2_files_ok,
            "missing_paths": missing_paths,
            "recommendations": recommendations,
            "all_ok": model_files_ok and ct2_files_ok
        }
        
        # Si hay problemas, setear error
        if not result["all_ok"]:
            self.model_loaded = False
            error_parts = ["Modelo no disponible:"]
            error_parts.extend([f"  - {path}" for path in missing_paths])
            if recommendations:
                error_parts.append("\nSolución:")
                error_parts.extend([f"  {rec}" for rec in recommendations])
            self.last_error = "\n".join(error_parts)
        
        return result
    
    def load(self) -> bool:
        """
        Carga el modelo NLLB y tokenizador.
        
        NO propaga excepciones - las captura y las almacena en last_error.
        
        Returns:
            True si la carga fue exitosa, False en caso contrario
        """
        if self.model_loaded:
            logger.info("Modelo ya cargado, omitiendo carga")
            return True
        
        self.load_started_at = datetime.now()
        logger.info("=" * 70)
        logger.info("Iniciando carga de modelo NLLB...")
        logger.info("=" * 70)
        
        try:
            # 1. Verificar rutas primero
            probe_result = self.probe_paths()
            if not probe_result["all_ok"]:
                logger.error(self.last_error)
                return False
            
            # 2. Cargar tokenizador HuggingFace
            logger.info(f"Cargando tokenizador desde {settings.MODEL_DIR}...")
            self.tokenizer = AutoTokenizer.from_pretrained(settings.MODEL_DIR)
            
            # 3. Configurar idioma source
            if hasattr(self.tokenizer, 'src_lang'):
                self.tokenizer.src_lang = settings.SOURCE_LANG
                logger.info(f"✓ Idioma source configurado: {settings.SOURCE_LANG}")
            
            # 4. Obtener token de idioma target
            if not hasattr(self.tokenizer, 'lang_code_to_id'):
                raise ValueError("El tokenizador no soporta lang_code_to_id (no es NLLB)")
            
            self.tgt_lang_id = self.tokenizer.lang_code_to_id.get(settings.TARGET_LANG)
            if self.tgt_lang_id is None:
                raise ValueError(f"No se encontró ID para idioma {settings.TARGET_LANG}")
            
            self.tgt_bos_tok = self.tokenizer.convert_ids_to_tokens(self.tgt_lang_id)
            logger.info(f"✓ Token idioma target: {self.tgt_bos_tok} (ID: {self.tgt_lang_id})")
            
            # 5. Cargar traductor CTranslate2
            logger.info(f"Cargando modelo CT2 desde {settings.CT2_DIR}...")
            self.translator = ct.Translator(
                settings.CT2_DIR,
                device="cpu",
                inter_threads=settings.CT2_INTER_THREADS if settings.CT2_INTER_THREADS > 0 else 0,
                intra_threads=settings.CT2_INTRA_THREADS if settings.CT2_INTRA_THREADS > 0 else 0,
                compute_type="int8"
            )
            logger.info("✓ Modelo CT2 cargado")
            
            # 6. Warmup (OMITIDO - causa hang en Windows con CTranslate2)
            # El modelo funciona perfectamente sin warmup
            logger.info("Omitiendo warmup (puede causar hang en Windows)")
            logger.info("✓ Modelo listo - primera traducción será ~2s más lenta")
            
            # 7. Marcar como cargado
            self.model_loaded = True
            self.last_error = None
            self.load_completed_at = datetime.now()
            load_time = (self.load_completed_at - self.load_started_at).total_seconds()
            
            logger.info("=" * 70)
            logger.info(f"✓ Modelo cargado exitosamente ({load_time:.1f}s)")
            logger.info("=" * 70)
            logger.info(f"  Modelo HF: {settings.MODEL_DIR}")
            logger.info(f"  Modelo CT2: {settings.CT2_DIR}")
            logger.info(f"  {settings.SOURCE_LANG} → {settings.TARGET_LANG}")
            logger.info("=" * 70)
            
            return True
            
        except Exception as e:
            # NO propagar - capturar y almacenar
            self.model_loaded = False
            error_msg = f"Error al cargar modelo: {type(e).__name__}: {str(e)}"
            
            # Stack trace corto (últimas 5 líneas)
            tb_lines = traceback.format_exc().split('\n')
            short_tb = '\n'.join(tb_lines[-6:-1])  # Últimas 5 líneas antes del final
            
            self.last_error = f"{error_msg}\n\nStack trace:\n{short_tb}"
            
            logger.error("=" * 70)
            logger.error("✗ Error al cargar modelo")
            logger.error("=" * 70)
            logger.error(self.last_error)
            logger.error("=" * 70)
            logger.error("La API seguirá funcionando pero /translate responderá 503")
            logger.error("Revisa /health para más detalles")
            logger.error("=" * 70)
            
            return False
    
    def health(self) -> dict:
        """
        Retorna información de salud y estado del modelo.
        
        Returns:
            Dict con estado completo del modelo
        """
        load_time_ms = None
        if self.load_started_at and self.load_completed_at:
            load_time_ms = int((self.load_completed_at - self.load_started_at).total_seconds() * 1000)
        
        return {
            "model_loaded": self.model_loaded,
            "last_error": self.last_error,
            "paths": {
                "model_dir": settings.MODEL_DIR,
                "ct2_dir": settings.CT2_DIR,
                "model_dir_exists": Path(settings.MODEL_DIR).exists(),
                "ct2_dir_exists": Path(settings.CT2_DIR).exists()
            },
            "config": {
                "source_lang": settings.SOURCE_LANG,
                "target_lang": settings.TARGET_LANG,
                "beam_size": settings.BEAM_SIZE,
                "inter_threads": settings.CT2_INTER_THREADS,
                "intra_threads": settings.CT2_INTRA_THREADS
            },
            "load_time_ms": load_time_ms
        }


# Instancia global singleton
model_manager = ModelManager()

