# Changelog

Todos los cambios notables del proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [1.0.0] - 2025-10-16

### ✨ Añadido
- Implementación inicial del servicio de traducción ES→DA
- Endpoint REST `/translate` con FastAPI
- Soporte para modelo NLLB-200 con CTranslate2
- Cuantización INT8 para inferencia eficiente
- Sistema de glosarios personalizados (pre/post procesamiento)
- Procesamiento batch de múltiples textos
- Scripts de descarga y conversión de modelos
- Makefile con comandos útiles
- Dockerfile para despliegue containerizado
- Tests smoke con pytest
- Documentación completa en README.md
- Variables de entorno para configuración
- Health checks y endpoints de información

### 🎯 Características
- 100% offline (después de descarga inicial)
- Soporte para modelos 600M y 1.3B
- API REST documentada con OpenAPI
- Control terminológico con glosarios
- Optimizado para CPU con multithreading

### 📚 Documentación
- README.md completo con ejemplos
- Guía de instalación local y Docker
- Troubleshooting y FAQ
- Ejemplos de uso en múltiples lenguajes
- Estructura del proyecto documentada

### 🐳 Docker
- Imagen basada en Python 3.11-slim
- Soporte para montaje de modelos como volumen
- Health checks integrados
- Variables de entorno configurables

### 🧪 Tests
- Tests de humo para funcionalidad básica
- Tests de validación de parámetros
- Tests de glosario
- Tests de batch processing

---

## [Unreleased]

### 🛣️ Roadmap
- Soporte para más pares de idiomas
- Cache de traducciones frecuentes
- API streaming para textos largos
- UI web para pruebas interactivas
- Métricas de calidad (BLEU, COMET)
- Soporte para INT4 quantization

---

**Leyenda:**
- ✨ Añadido: Nuevas funcionalidades
- 🔧 Cambiado: Cambios en funcionalidad existente
- 🐛 Corregido: Bugs arreglados
- 🗑️ Eliminado: Funcionalidad removida
- 🔒 Seguridad: Vulnerabilidades corregidas

