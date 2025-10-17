#!/bin/bash
# Script para convertir modelo NLLB a CTranslate2 con quantization INT8
#
# Uso:
#   bash scripts/convert_to_ct2.sh --in models/nllb-600m --out models/nllb-600m-ct2-int8

set -euo pipefail

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Variables
INPUT_DIR=""
OUTPUT_DIR=""

# Parsear argumentos
while [[ $# -gt 0 ]]; do
    case $1 in
        --in)
            INPUT_DIR="$2"
            shift 2
            ;;
        --out)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        *)
            echo -e "${RED}Error: Argumento desconocido: $1${NC}"
            echo "Uso: $0 --in <input_dir> --out <output_dir>"
            exit 1
            ;;
    esac
done

# Validar argumentos
if [ -z "$INPUT_DIR" ] || [ -z "$OUTPUT_DIR" ]; then
    echo -e "${RED}Error: Faltan argumentos${NC}"
    echo "Uso: $0 --in <input_dir> --out <output_dir>"
    echo ""
    echo "Ejemplo:"
    echo "  $0 --in models/nllb-600m --out models/nllb-600m-ct2-int8"
    exit 1
fi

# Verificar que existe el directorio de input
if [ ! -d "$INPUT_DIR" ]; then
    echo -e "${RED}Error: Directorio de entrada no existe: $INPUT_DIR${NC}"
    echo ""
    echo "Primero descarga el modelo ejecutando:"
    echo "  python scripts/download_model.py --model facebook/nllb-200-distilled-600M --out $INPUT_DIR"
    echo "O simplemente:"
    echo "  make download"
    exit 1
fi

# Información
echo "======================================================================"
echo -e "${GREEN}Convirtiendo modelo NLLB a CTranslate2 (INT8)${NC}"
echo "======================================================================"
echo "Entrada:  $INPUT_DIR"
echo "Salida:   $OUTPUT_DIR"
echo "Quantization: INT8"
echo "======================================================================"
echo ""

# Verificar que ct2-transformers-converter está instalado
if ! command -v ct2-transformers-converter &> /dev/null; then
    echo -e "${RED}Error: ct2-transformers-converter no está instalado${NC}"
    echo ""
    echo "Instala CTranslate2 ejecutando:"
    echo "  pip install ctranslate2"
    echo "O:"
    echo "  make venv"
    exit 1
fi

# Crear directorio de salida
mkdir -p "$OUTPUT_DIR"

# Convertir modelo
echo -e "${YELLOW}Convirtiendo modelo... (esto puede tardar varios minutos)${NC}"
echo ""

ct2-transformers-converter \
    --model "$INPUT_DIR" \
    --output_dir "$OUTPUT_DIR" \
    --quantization int8 \
    --force

# Verificar resultado
if [ $? -eq 0 ]; then
    echo ""
    echo "======================================================================"
    echo -e "${GREEN}✓ Conversión completada exitosamente${NC}"
    echo "======================================================================"
    echo "Modelo CT2 INT8 guardado en: $OUTPUT_DIR"
    echo ""
    echo "Archivos generados:"
    ls -lh "$OUTPUT_DIR"
    echo ""
    echo "======================================================================"
    echo "Siguiente paso:"
    echo "  Inicia el servidor ejecutando:"
    echo "    make run"
    echo "  O con Docker:"
    echo "    make docker-build && make docker-run"
    echo "======================================================================"
else
    echo ""
    echo "======================================================================"
    echo -e "${RED}✗ Error en la conversión${NC}"
    echo "======================================================================"
    echo "Verifica que:"
    echo "  1. El directorio de entrada contiene un modelo HuggingFace válido"
    echo "  2. Tienes suficiente espacio en disco (~2-3x el tamaño del modelo)"
    echo "  3. Tienes permisos de escritura en el directorio de salida"
    echo "======================================================================"
    exit 1
fi

