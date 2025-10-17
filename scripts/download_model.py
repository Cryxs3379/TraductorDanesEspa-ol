#!/usr/bin/env python3
"""
Script para descargar modelos NLLB desde HuggingFace Hub.

Uso:
    python scripts/download_model.py --model facebook/nllb-200-distilled-600M --out models/nllb-600m
"""
import argparse
import logging
import sys
from pathlib import Path

from huggingface_hub import snapshot_download


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def download_model(model_name: str, output_dir: str):
    """
    Descarga un modelo desde HuggingFace Hub.
    
    Args:
        model_name: Nombre del modelo en HuggingFace (ej: facebook/nllb-200-distilled-600M)
        output_dir: Directorio de salida donde se guardará el modelo
    """
    output_path = Path(output_dir)
    
    logger.info("=" * 70)
    logger.info("Descargando modelo NLLB")
    logger.info("=" * 70)
    logger.info(f"Modelo: {model_name}")
    logger.info(f"Destino: {output_path.absolute()}")
    logger.info("=" * 70)
    
    # Crear directorio si no existe
    output_path.mkdir(parents=True, exist_ok=True)
    
    try:
        logger.info("Iniciando descarga... (esto puede tardar varios minutos)")
        logger.info("Consejo: Asegúrate de tener espacio suficiente en disco:")
        logger.info("  - nllb-200-distilled-600M: ~2.4 GB")
        logger.info("  - nllb-200-1.3B: ~5 GB")
        logger.info("")
        
        # Descargar modelo
        snapshot_download(
            repo_id=model_name,
            local_dir=output_dir,
            local_dir_use_symlinks=False,  # Copiar archivos en vez de symlinks
            resume_download=True  # Permitir reanudar si se interrumpe
        )
        
        logger.info("=" * 70)
        logger.info("✓ Descarga completada exitosamente")
        logger.info("=" * 70)
        logger.info(f"Modelo guardado en: {output_path.absolute()}")
        logger.info("")
        logger.info("Siguiente paso:")
        logger.info(f"  Convierte el modelo a CTranslate2 ejecutando:")
        logger.info(f"  bash scripts/convert_to_ct2.sh --in {output_dir} --out {output_dir}-ct2-int8")
        logger.info("  O simplemente:")
        logger.info(f"  make convert")
        logger.info("=" * 70)
        
    except KeyboardInterrupt:
        logger.warning("\n⚠ Descarga interrumpida por el usuario")
        logger.info("Puedes reanudar la descarga ejecutando el mismo comando")
        sys.exit(1)
    except Exception as e:
        logger.error("=" * 70)
        logger.error(f"✗ Error al descargar modelo: {e}")
        logger.error("=" * 70)
        logger.error("\nPosibles causas:")
        logger.error("  1. Sin conexión a Internet")
        logger.error("  2. Nombre de modelo incorrecto")
        logger.error("  3. Espacio en disco insuficiente")
        logger.error("  4. Permisos de escritura insuficientes")
        logger.error("")
        logger.error(f"Nombre del modelo: {model_name}")
        logger.error("Verifica que el nombre sea correcto en HuggingFace Hub")
        logger.error("=" * 70)
        sys.exit(1)


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="Descarga modelos NLLB desde HuggingFace Hub",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Descargar modelo 600M (recomendado para RAM >= 8GB)
  python scripts/download_model.py \\
      --model facebook/nllb-200-distilled-600M \\
      --out models/nllb-600m

  # Descargar modelo 1.3B (recomendado para RAM >= 16GB)
  python scripts/download_model.py \\
      --model facebook/nllb-200-1.3B \\
      --out models/nllb-1.3b

Modelos disponibles:
  - facebook/nllb-200-distilled-600M (~2.4 GB)
  - facebook/nllb-200-1.3B (~5 GB)
  - facebook/nllb-200-3.3B (~13 GB) - requiere mucha RAM
        """
    )
    
    parser.add_argument(
        "--model",
        type=str,
        required=True,
        help="Nombre del modelo en HuggingFace (ej: facebook/nllb-200-distilled-600M)"
    )
    
    parser.add_argument(
        "--out",
        type=str,
        required=True,
        help="Directorio de salida donde guardar el modelo"
    )
    
    args = parser.parse_args()
    
    # Descargar
    download_model(args.model, args.out)


if __name__ == "__main__":
    main()

