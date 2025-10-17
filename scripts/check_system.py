#!/usr/bin/env python3
"""
Script de verificación del sistema para el traductor ES→DA.

Verifica que todos los requisitos estén instalados y configurados correctamente.
"""
import sys
import os
import platform
import subprocess
from pathlib import Path


def print_header(text):
    """Imprime un encabezado formateado."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_check(name, status, details=""):
    """Imprime el resultado de una verificación."""
    symbol = "✓" if status else "✗"
    color = "\033[92m" if status else "\033[91m"
    reset = "\033[0m"
    
    print(f"{color}{symbol}{reset} {name}")
    if details:
        print(f"  → {details}")


def check_python_version():
    """Verifica la versión de Python."""
    version = sys.version_info
    required = (3, 11)
    
    is_ok = version >= required
    details = f"Python {version.major}.{version.minor}.{version.micro}"
    
    if not is_ok:
        details += f" (requiere {required[0]}.{required[1]}+)"
    
    print_check("Python 3.11+", is_ok, details)
    return is_ok


def check_package(package_name):
    """Verifica si un paquete está instalado."""
    try:
        __import__(package_name)
        return True
    except ImportError:
        return False


def check_dependencies():
    """Verifica las dependencias principales."""
    packages = {
        "fastapi": "FastAPI",
        "uvicorn": "Uvicorn",
        "transformers": "Transformers",
        "ctranslate2": "CTranslate2",
        "sentencepiece": "SentencePiece",
        "pydantic": "Pydantic",
        "pytest": "Pytest"
    }
    
    all_ok = True
    for pkg_name, display_name in packages.items():
        is_installed = check_package(pkg_name)
        print_check(display_name, is_installed)
        all_ok = all_ok and is_installed
    
    return all_ok


def check_model_files():
    """Verifica que los modelos existan."""
    model_dir = os.getenv("MODEL_DIR", "./models/nllb-600m")
    ct2_dir = os.getenv("CT2_DIR", "./models/nllb-600m-ct2-int8")
    
    model_exists = Path(model_dir).exists()
    ct2_exists = Path(ct2_dir).exists()
    
    print_check("Modelo HF descargado", model_exists, model_dir)
    print_check("Modelo CT2 convertido", ct2_exists, ct2_dir)
    
    return model_exists and ct2_exists


def check_disk_space():
    """Verifica el espacio en disco disponible."""
    try:
        if platform.system() == "Windows":
            import shutil
            total, used, free = shutil.disk_usage(".")
        else:
            import shutil
            total, used, free = shutil.disk_usage(".")
        
        free_gb = free // (2**30)
        is_ok = free_gb >= 5
        
        print_check(
            "Espacio en disco",
            is_ok,
            f"{free_gb} GB disponibles (requiere 5+ GB)"
        )
        return is_ok
    except Exception as e:
        print_check("Espacio en disco", False, f"Error: {e}")
        return False


def check_memory():
    """Verifica la memoria RAM disponible."""
    try:
        if platform.system() == "Linux":
            with open('/proc/meminfo', 'r') as f:
                lines = f.readlines()
                mem_total = int([l for l in lines if 'MemTotal' in l][0].split()[1]) // 1024
                mem_available = int([l for l in lines if 'MemAvailable' in l][0].split()[1]) // 1024
        elif platform.system() == "Darwin":  # macOS
            vm = subprocess.check_output(['vm_stat']).decode()
            # Simplificado - solo mostrar que hay RAM
            mem_total = "N/A"
            mem_available = "N/A"
        elif platform.system() == "Windows":
            # Windows - usar wmic o psutil si está disponible
            try:
                import psutil
                mem = psutil.virtual_memory()
                mem_total = mem.total // (1024**2)
                mem_available = mem.available // (1024**2)
            except ImportError:
                mem_total = "N/A"
                mem_available = "N/A"
        else:
            mem_total = "N/A"
            mem_available = "N/A"
        
        if mem_total != "N/A" and mem_available != "N/A":
            is_ok = mem_total >= 8000  # 8 GB
            print_check(
                "Memoria RAM",
                is_ok,
                f"{mem_total} MB total, {mem_available} MB disponible (requiere 8+ GB)"
            )
            return is_ok
        else:
            print_check("Memoria RAM", True, "No se pudo verificar automáticamente")
            return True
            
    except Exception as e:
        print_check("Memoria RAM", True, f"No se pudo verificar: {e}")
        return True


def check_port():
    """Verifica si el puerto 8000 está disponible."""
    import socket
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 8000))
        sock.close()
        
        if result == 0:
            print_check("Puerto 8000", False, "Puerto ocupado (¿servidor corriendo?)")
            return False
        else:
            print_check("Puerto 8000", True, "Puerto disponible")
            return True
    except Exception as e:
        print_check("Puerto 8000", True, f"No se pudo verificar: {e}")
        return True


def check_ct2_converter():
    """Verifica que ct2-transformers-converter esté disponible."""
    try:
        result = subprocess.run(
            ['ct2-transformers-converter', '--help'],
            capture_output=True,
            timeout=5
        )
        is_ok = result.returncode == 0
        print_check("ct2-transformers-converter", is_ok)
        return is_ok
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print_check("ct2-transformers-converter", False, "No encontrado")
        return False


def main():
    """Función principal."""
    print_header("Verificación del Sistema - Traductor ES→DA")
    
    print("\n📋 Sistema Operativo:")
    print(f"  {platform.system()} {platform.release()}")
    print(f"  {platform.machine()}")
    
    print_header("1. Versión de Python")
    python_ok = check_python_version()
    
    print_header("2. Dependencias Python")
    deps_ok = check_dependencies()
    
    print_header("3. Modelos")
    models_ok = check_model_files()
    
    print_header("4. Recursos del Sistema")
    disk_ok = check_disk_space()
    mem_ok = check_memory()
    
    print_header("5. Configuración del Servidor")
    port_ok = check_port()
    
    print_header("6. Herramientas de Conversión")
    converter_ok = check_ct2_converter()
    
    # Resumen final
    print_header("Resumen")
    
    all_checks = {
        "Python 3.11+": python_ok,
        "Dependencias": deps_ok,
        "Modelos": models_ok,
        "Espacio en disco": disk_ok,
        "Memoria RAM": mem_ok,
        "Puerto disponible": port_ok,
        "Conversor CT2": converter_ok
    }
    
    passed = sum(all_checks.values())
    total = len(all_checks)
    
    print(f"\n✓ Pasadas: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 ¡Todo listo! Puedes ejecutar:")
        print("     make run")
    else:
        print("\n⚠️  Hay problemas que resolver:")
        for check, status in all_checks.items():
            if not status:
                print(f"     ✗ {check}")
        
        print("\nSoluciones sugeridas:")
        if not deps_ok:
            print("  - Instalar dependencias: make venv")
        if not models_ok:
            print("  - Descargar modelo: make download")
            print("  - Convertir modelo: make convert")
        if not disk_ok:
            print("  - Liberar espacio en disco")
        if not converter_ok:
            print("  - Instalar CTranslate2: pip install ctranslate2")
    
    print("\n" + "=" * 70)
    print()
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

