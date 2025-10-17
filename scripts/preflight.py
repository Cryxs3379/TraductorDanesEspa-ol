#!/usr/bin/env python3
"""
Script de preflight para verificar el entorno antes de iniciar el servidor.

Verifica:
- Versión de Python
- RAM libre estimada
- Espacio en disco
- Existencia de modelos
- Dependencias instaladas
"""
import sys
import os
import platform
import shutil
from pathlib import Path


def check_python_version():
    """Verifica la versión de Python."""
    version = sys.version_info
    print(f"🐍 Python: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print("   ⚠️  Se recomienda Python 3.9+")
        return False
    else:
        print("   ✓ Versión adecuada")
        return True


def check_ram():
    """Estima RAM libre disponible."""
    try:
        if platform.system() == "Linux":
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if 'MemAvailable' in line:
                        # En KB
                        mem_kb = int(line.split()[1])
                        mem_gb = mem_kb / (1024 ** 2)
                        print(f"💾 RAM disponible: {mem_gb:.1f} GB")
                        
                        if mem_gb < 8:
                            print("   ⚠️  Se recomienda >= 8GB para modelo 600M")
                            return False
                        else:
                            print("   ✓ Suficiente RAM")
                            return True
                        break
        elif platform.system() == "Windows":
            import ctypes
            kernel32 = ctypes.windll.kernel32
            c_ulong = ctypes.c_ulong
            class MEMORYSTATUS(ctypes.Structure):
                _fields_ = [
                    ('dwLength', c_ulong),
                    ('dwMemoryLoad', c_ulong),
                    ('dwTotalPhys', c_ulong),
                    ('dwAvailPhys', c_ulong),
                    ('dwTotalPageFile', c_ulong),
                    ('dwAvailPageFile', c_ulong),
                    ('dwTotalVirtual', c_ulong),
                    ('dwAvailVirtual', c_ulong)
                ]
            
            mem_status = MEMORYSTATUS()
            mem_status.dwLength = ctypes.sizeof(MEMORYSTATUS)
            kernel32.GlobalMemoryStatus(ctypes.byref(mem_status))
            
            avail_gb = mem_status.dwAvailPhys / (1024 ** 3)
            print(f"💾 RAM disponible: {avail_gb:.1f} GB")
            
            if avail_gb < 8:
                print("   ⚠️  Se recomienda >= 8GB para modelo 600M")
                return False
            else:
                print("   ✓ Suficiente RAM")
                return True
        else:
            print("💾 RAM: No se pudo determinar (sistema no soportado)")
            return True
    except Exception as e:
        print(f"💾 RAM: No se pudo determinar ({e})")
        return True


def check_disk_space():
    """Verifica espacio en disco."""
    try:
        usage = shutil.disk_usage(Path.cwd())
        free_gb = usage.free / (1024 ** 3)
        print(f"💿 Espacio libre: {free_gb:.1f} GB")
        
        if free_gb < 5:
            print("   ⚠️  Se recomienda >= 5GB libres")
            return False
        else:
            print("   ✓ Espacio suficiente")
            return True
    except Exception as e:
        print(f"💿 Espacio en disco: No se pudo determinar ({e})")
        return True


def check_model_paths():
    """Verifica la existencia de los modelos."""
    model_dir = Path(os.getenv("MODEL_DIR", "./models/nllb-600m"))
    ct2_dir = Path(os.getenv("CT2_DIR", "./models/nllb-600m-ct2-int8"))
    
    print(f"\n📁 Modelos:")
    print(f"   HF: {model_dir}")
    
    model_ok = False
    if model_dir.exists():
        # Verificar archivos clave
        has_config = (model_dir / "config.json").exists()
        has_weights = (model_dir / "pytorch_model.bin").exists() or (model_dir / "model.safetensors").exists()
        
        if has_config and has_weights:
            print(f"   ✓ Modelo HuggingFace encontrado")
            model_ok = True
        else:
            print(f"   ⚠️  Modelo HuggingFace incompleto")
            print(f"       Ejecuta: make download")
    else:
        print(f"   ✗ Modelo HuggingFace NO encontrado")
        print(f"       Ejecuta: make download")
    
    print(f"   CT2: {ct2_dir}")
    ct2_ok = False
    if ct2_dir.exists():
        has_model = (ct2_dir / "model.bin").exists()
        has_config = (ct2_dir / "config.json").exists()
        
        if has_model and has_config:
            print(f"   ✓ Modelo CTranslate2 encontrado")
            ct2_ok = True
        else:
            print(f"   ⚠️  Modelo CTranslate2 incompleto")
            print(f"       Ejecuta: make convert")
    else:
        print(f"   ✗ Modelo CTranslate2 NO encontrado")
        print(f"       Ejecuta: make convert")
    
    return model_ok and ct2_ok


def check_dependencies():
    """Verifica dependencias clave."""
    print(f"\n📦 Dependencias:")
    
    deps = {
        "fastapi": "FastAPI",
        "uvicorn": "Uvicorn",
        "ctranslate2": "CTranslate2",
        "transformers": "Transformers",
        "sentencepiece": "SentencePiece"
    }
    
    all_ok = True
    for module, name in deps.items():
        try:
            __import__(module)
            print(f"   ✓ {name}")
        except ImportError:
            print(f"   ✗ {name} NO instalado")
            all_ok = False
    
    if not all_ok:
        print(f"\n   Ejecuta: pip install -r requirements.txt")
    
    return all_ok


def main():
    """Función principal."""
    print("=" * 70)
    print("Preflight Check - Traductor ES→DA")
    print("=" * 70)
    print()
    
    checks = []
    
    # Verificaciones
    checks.append(("Python", check_python_version()))
    checks.append(("RAM", check_ram()))
    checks.append(("Espacio", check_disk_space()))
    checks.append(("Modelos", check_model_paths()))
    checks.append(("Dependencias", check_dependencies()))
    
    # Resumen
    print()
    print("=" * 70)
    print("Resumen:")
    print("=" * 70)
    
    all_ok = True
    for name, ok in checks:
        status = "✓" if ok else "✗"
        print(f"  {status} {name}")
        if not ok:
            all_ok = False
    
    print("=" * 70)
    
    if all_ok:
        print("✓ Sistema listo para ejecutar: make run")
        return 0
    else:
        print("⚠️  Hay problemas que resolver antes de ejecutar")
        print("\nSoluciones comunes:")
        print("  1. make venv          # Crear entorno e instalar deps")
        print("  2. make download      # Descargar modelo NLLB")
        print("  3. make convert       # Convertir a CTranslate2")
        print("  4. make run           # Iniciar servidor")
        return 1


if __name__ == "__main__":
    sys.exit(main())

