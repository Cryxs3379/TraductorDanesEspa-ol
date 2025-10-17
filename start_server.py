"""Script para iniciar el servidor con mejor manejo de errores"""
import os
import sys

# Configurar variables de entorno
os.environ["MODEL_DIR"] = "./models/nllb-600m"
os.environ["CT2_DIR"] = "./models/nllb-600m-ct2-int8"

print("=" * 70)
print("Iniciando servidor de traduccion ES->DA")
print("=" * 70)
print(f"Python: {sys.version}")
print(f"MODEL_DIR: {os.environ['MODEL_DIR']}")
print(f"CT2_DIR: {os.environ['CT2_DIR']}")
print("=" * 70)
print()

try:
    import uvicorn
    print("✓ uvicorn importado")
    
    from app.app import app
    print("✓ app importada")
    
    print()
    print("Iniciando servidor en http://localhost:8000")
    print("Presiona Ctrl+C para detener")
    print("=" * 70)
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
except Exception as e:
    print()
    print("=" * 70)
    print("ERROR al iniciar el servidor:")
    print("=" * 70)
    print(f"{type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

