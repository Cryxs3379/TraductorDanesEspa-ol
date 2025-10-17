#!/usr/bin/env python3
"""
Ejemplos de uso del API de traducción ES→DA.

Asegúrate de que el servidor esté corriendo:
    make run
    # o
    uvicorn app.app:app --host 0.0.0.0 --port 8000
"""
import requests
import json
from typing import List, Dict, Any


# URL base del API
BASE_URL = "http://localhost:8000"


def translate_single(text: str, max_tokens: int = 256) -> str:
    """
    Traduce un solo texto.
    
    Args:
        text: Texto en español
        max_tokens: Máximo de tokens a generar
        
    Returns:
        Traducción en danés
    """
    response = requests.post(
        f"{BASE_URL}/translate",
        json={
            "text": text,
            "max_new_tokens": max_tokens
        }
    )
    response.raise_for_status()
    data = response.json()
    return data["translations"][0]


def translate_batch(texts: List[str], max_tokens: int = 256) -> List[str]:
    """
    Traduce múltiples textos en batch.
    
    Args:
        texts: Lista de textos en español
        max_tokens: Máximo de tokens a generar
        
    Returns:
        Lista de traducciones en danés
    """
    response = requests.post(
        f"{BASE_URL}/translate",
        json={
            "text": texts,
            "max_new_tokens": max_tokens
        }
    )
    response.raise_for_status()
    data = response.json()
    return data["translations"]


def translate_with_glossary(
    text: str,
    glossary: Dict[str, str],
    max_tokens: int = 256
) -> str:
    """
    Traduce con un glosario personalizado.
    
    Args:
        text: Texto en español
        glossary: Diccionario de términos ES→DA
        max_tokens: Máximo de tokens a generar
        
    Returns:
        Traducción en danés con glosario aplicado
    """
    response = requests.post(
        f"{BASE_URL}/translate",
        json={
            "text": text,
            "glossary": glossary,
            "max_new_tokens": max_tokens
        }
    )
    response.raise_for_status()
    data = response.json()
    return data["translations"][0]


def check_health() -> Dict[str, Any]:
    """Verifica el estado del servicio."""
    response = requests.get(f"{BASE_URL}/health")
    response.raise_for_status()
    return response.json()


def get_info() -> Dict[str, Any]:
    """Obtiene información del modelo y capacidades."""
    response = requests.get(f"{BASE_URL}/info")
    response.raise_for_status()
    return response.json()


def main():
    """Función principal con ejemplos."""
    
    print("=" * 70)
    print("Ejemplos de Traducción ES→DA")
    print("=" * 70)
    print()
    
    # Verificar que el servicio esté online
    print("1. Verificando estado del servicio...")
    try:
        health = check_health()
        print(f"   ✓ Estado: {health['status']}")
        print()
    except requests.exceptions.RequestException as e:
        print(f"   ✗ Error: No se pudo conectar al servicio")
        print(f"   Asegúrate de que esté corriendo: make run")
        print(f"   Error: {e}")
        return
    
    # Ejemplo 1: Traducción simple
    print("2. Traducción simple:")
    text1 = "Hola mundo"
    translation1 = translate_single(text1)
    print(f"   ES: {text1}")
    print(f"   DA: {translation1}")
    print()
    
    # Ejemplo 2: Traducción batch
    print("3. Traducción batch (múltiples textos):")
    texts = [
        "Buenos días",
        "¿Cómo estás?",
        "Gracias por tu ayuda",
        "Hasta luego"
    ]
    translations = translate_batch(texts)
    for es, da in zip(texts, translations):
        print(f"   ES: {es}")
        print(f"   DA: {da}")
        print()
    
    # Ejemplo 3: Traducción con glosario
    print("4. Traducción con glosario personalizado:")
    text3 = "Bienvenido a Acme Corporation. Python es un lenguaje de programación."
    glossary = {
        "Acme": "Acme",  # Preservar nombre de empresa
        "Corporation": "Selskab",  # Término específico
        "Python": "Python"  # Preservar nombre de lenguaje
    }
    translation3 = translate_with_glossary(text3, glossary)
    print(f"   ES: {text3}")
    print(f"   DA: {translation3}")
    print(f"   Glosario: {json.dumps(glossary, indent=6)}")
    print()
    
    # Ejemplo 4: Información del modelo
    print("5. Información del modelo:")
    info = get_info()
    print(f"   Modelo: {info['model']['model_dir']}")
    print(f"   Idiomas: {info['model']['source_lang']} → {info['model']['target_lang']}")
    print(f"   Soporta glosarios: {info['capabilities']['supports_glossary']}")
    print(f"   Soporta batch: {info['capabilities']['supports_batch']}")
    print()
    
    # Ejemplo 5: Textos más largos
    print("6. Traducción de texto largo:")
    long_text = (
        "La inteligencia artificial está transformando el mundo. "
        "Los modelos de lenguaje como NLLB permiten traducir entre "
        "cientos de idiomas con alta calidad. Esta tecnología es "
        "accesible, gratuita y puede ejecutarse localmente sin "
        "necesidad de conexión a Internet."
    )
    long_translation = translate_single(long_text, max_tokens=512)
    print(f"   ES: {long_text}")
    print(f"   DA: {long_translation}")
    print()
    
    print("=" * 70)
    print("✓ Ejemplos completados")
    print("=" * 70)


if __name__ == "__main__":
    main()

