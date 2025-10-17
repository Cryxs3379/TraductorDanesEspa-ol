#!/usr/bin/env python3
"""
Script de arranque del servidor con detección automática de puerto libre.

Intenta usar el puerto configurado (default 8000). Si está ocupado,
busca el siguiente puerto libre automáticamente.
"""
import os
import sys
import uvicorn

# Añadir directorio actual al path para imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.settings import settings, pick_free_port


def main():
    """Función principal."""
    print("=" * 70)
    print("Iniciando Traductor ES→DA")
    print("=" * 70)
    
    # Encontrar puerto libre
    try:
        port = pick_free_port(settings.PORT)
    except RuntimeError as e:
        print(f"✗ Error: {e}")
        print("   No se pudo encontrar un puerto libre")
        return 1
    
    print(f"Puerto: {port}")
    print(f"Host: {settings.HOST}")
    print("=" * 70)
    print()
    print(f"🌐 API disponible en: http://localhost:{port}")
    print(f"📚 Documentación: http://localhost:{port}/docs")
    print(f"❤️  Health check: http://localhost:{port}/health")
    print()
    print("Presiona Ctrl+C para detener el servidor")
    print("=" * 70)
    print()
    
    # Iniciar servidor
    try:
        uvicorn.run(
            "app.app:app",
            host=settings.HOST,
            port=port,
            reload=False,
            log_level="info",
            access_log=not settings.LOG_TRANSLATIONS  # Desactivar si no queremos logs de acceso
        )
    except KeyboardInterrupt:
        print("\n\n" + "=" * 70)
        print("Servidor detenido")
        print("=" * 70)
        return 0
    except Exception as e:
        print(f"\n✗ Error al iniciar servidor: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
