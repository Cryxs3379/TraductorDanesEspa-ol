#!/usr/bin/env python3
"""Script de diagnóstico para probar la carga del modelo."""
import sys
import os

# Asegurar que estamos en el directorio correcto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("TEST DE CARGA DEL MODELO")
print("=" * 70)

print("\n1. Importando modulos...")
try:
    from app.settings import settings
    print(f"   [OK] Settings importado")
    print(f"     MODEL_DIR: {settings.MODEL_DIR}")
    print(f"     CT2_DIR: {settings.CT2_DIR}")
except Exception as e:
    print(f"   [ERROR] Error importando settings: {e}")
    sys.exit(1)

print("\n2. Verificando rutas...")
from pathlib import Path
model_dir = Path(settings.MODEL_DIR)
ct2_dir = Path(settings.CT2_DIR)

print(f"   Modelo HF: {model_dir.absolute()}")
print(f"     Existe: {model_dir.exists()}")
if model_dir.exists():
    files = list(model_dir.iterdir())
    print(f"     Archivos: {len(files)}")
    for f in files[:5]:
        print(f"       - {f.name}")

print(f"   Modelo CT2: {ct2_dir.absolute()}")
print(f"     Existe: {ct2_dir.exists()}")
if ct2_dir.exists():
    files = list(ct2_dir.iterdir())
    print(f"     Archivos: {len(files)}")
    for f in files:
        print(f"       - {f.name}")

print("\n3. Intentando cargar ModelManager...")
try:
    from app.startup import model_manager
    print(f"   [OK] ModelManager creado")
except Exception as e:
    print(f"   [ERROR] Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n4. Ejecutando probe_paths()...")
try:
    probe = model_manager.probe_paths()
    print(f"   Resultado: {probe}")
except Exception as e:
    print(f"   [ERROR] Error: {e}")
    import traceback
    traceback.print_exc()

print("\n5. Intentando cargar modelo...")
try:
    result = model_manager.load()
    print(f"   Resultado: {result}")
    print(f"   model_loaded: {model_manager.model_loaded}")
    print(f"   last_error: {model_manager.last_error}")
    
    if result:
        print("\n[OK] MODELO CARGADO EXITOSAMENTE!")
    else:
        print("\n[ERROR] Fallo al cargar modelo")
        if model_manager.last_error:
            print("\nError completo:")
            print(model_manager.last_error)
            
except Exception as e:
    print(f"   [ERROR] Excepcion: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)

