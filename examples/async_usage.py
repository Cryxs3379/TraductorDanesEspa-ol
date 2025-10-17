#!/usr/bin/env python3
"""
Ejemplos de uso asíncrono del API de traducción ES→DA.

Útil para aplicaciones asíncronas con asyncio/aiohttp.
"""
import asyncio
import aiohttp
from typing import List, Dict, Any


BASE_URL = "http://localhost:8000"


async def translate_single_async(
    session: aiohttp.ClientSession,
    text: str,
    max_tokens: int = 256
) -> str:
    """Traduce un texto de forma asíncrona."""
    async with session.post(
        f"{BASE_URL}/translate",
        json={
            "text": text,
            "max_new_tokens": max_tokens
        }
    ) as response:
        data = await response.json()
        return data["translations"][0]


async def translate_batch_async(
    session: aiohttp.ClientSession,
    texts: List[str],
    max_tokens: int = 256
) -> List[str]:
    """Traduce múltiples textos de forma asíncrona."""
    async with session.post(
        f"{BASE_URL}/translate",
        json={
            "text": texts,
            "max_new_tokens": max_tokens
        }
    ) as response:
        data = await response.json()
        return data["translations"]


async def translate_many_concurrent(texts: List[str]) -> List[str]:
    """
    Traduce muchos textos de forma concurrente.
    
    Envía múltiples requests en paralelo para máximo throughput.
    """
    async with aiohttp.ClientSession() as session:
        tasks = [
            translate_single_async(session, text)
            for text in texts
        ]
        return await asyncio.gather(*tasks)


async def main():
    """Función principal asíncrona."""
    
    print("=" * 70)
    print("Ejemplos de Traducción Asíncrona ES→DA")
    print("=" * 70)
    print()
    
    async with aiohttp.ClientSession() as session:
        # Ejemplo 1: Traducción simple asíncrona
        print("1. Traducción simple asíncrona:")
        text = "Hola mundo asíncrono"
        translation = await translate_single_async(session, text)
        print(f"   ES: {text}")
        print(f"   DA: {translation}")
        print()
        
        # Ejemplo 2: Batch asíncrono
        print("2. Traducción batch asíncrona:")
        texts = [
            "Buenos días",
            "¿Cómo estás?",
            "Excelente día"
        ]
        translations = await translate_batch_async(session, texts)
        for es, da in zip(texts, translations):
            print(f"   ES: {es} → DA: {da}")
        print()
    
    # Ejemplo 3: Muchas traducciones concurrentes
    print("3. Traducciones concurrentes (requests paralelos):")
    many_texts = [
        f"Texto número {i+1} para traducir"
        for i in range(10)
    ]
    
    import time
    start = time.time()
    results = await translate_many_concurrent(many_texts)
    elapsed = time.time() - start
    
    print(f"   ✓ Traducidos {len(results)} textos en {elapsed:.2f}s")
    print(f"   Throughput: {len(results)/elapsed:.1f} textos/segundo")
    print()
    
    for i, (es, da) in enumerate(zip(many_texts[:3], results[:3]), 1):
        print(f"   {i}. {es} → {da}")
    print(f"   ... (y {len(results)-3} más)")
    print()
    
    print("=" * 70)
    print("✓ Ejemplos asíncronos completados")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())

