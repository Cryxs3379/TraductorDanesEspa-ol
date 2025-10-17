#!/bin/bash
# Ejemplos de uso del API con cURL

BASE_URL="http://localhost:8000"

echo "======================================================================"
echo "Ejemplos de Traducción ES→DA con cURL"
echo "======================================================================"
echo ""

# Verificar que el servicio esté corriendo
echo "1. Health Check:"
curl -s "$BASE_URL/health" | python -m json.tool
echo ""
echo "======================================================================"
echo ""

# Ejemplo 1: Traducción simple
echo "2. Traducción simple:"
echo "   Texto: 'Hola mundo'"
echo ""
curl -s -X POST "$BASE_URL/translate" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hola mundo",
    "max_new_tokens": 128
  }' | python -m json.tool
echo ""
echo "======================================================================"
echo ""

# Ejemplo 2: Traducción batch
echo "3. Traducción batch (múltiples textos):"
echo ""
curl -s -X POST "$BASE_URL/translate" \
  -H "Content-Type: application/json" \
  -d '{
    "text": [
      "Buenos días",
      "¿Cómo estás?",
      "Gracias"
    ],
    "max_new_tokens": 128
  }' | python -m json.tool
echo ""
echo "======================================================================"
echo ""

# Ejemplo 3: Con glosario
echo "4. Traducción con glosario:"
echo "   Texto: 'Bienvenido a Python'"
echo "   Glosario: Python → Python (preservar)"
echo ""
curl -s -X POST "$BASE_URL/translate" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Bienvenido a Python",
    "glossary": {
      "Python": "Python"
    },
    "max_new_tokens": 128
  }' | python -m json.tool
echo ""
echo "======================================================================"
echo ""

# Ejemplo 4: Texto largo
echo "5. Traducción de texto largo:"
echo ""
curl -s -X POST "$BASE_URL/translate" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "La inteligencia artificial está transformando el mundo. Los modelos de lenguaje permiten traducir entre cientos de idiomas.",
    "max_new_tokens": 256
  }' | python -m json.tool
echo ""
echo "======================================================================"
echo ""

# Información del modelo
echo "6. Información del modelo:"
echo ""
curl -s "$BASE_URL/info" | python -m json.tool
echo ""
echo "======================================================================"
echo ""

echo "✓ Ejemplos completados"

