#!/usr/bin/env python3
"""
Creador multiplataforma de paquetes de despliegue para Lambda usando uv.
Funciona en Windows, Mac y Linux.
"""

import os
import sys
import shutil
import zipfile
from pathlib import Path


def create_deployment_package():
    """Crea un paquete de despliegue Lambda con dependencias de uv."""
    
    # Rutas
    current_dir = Path(__file__).parent
    build_dir = current_dir / 'build'
    package_dir = build_dir / 'package'
    zip_path = current_dir / 'lambda_function.zip'
    venv_site_packages = current_dir / '.venv' / 'lib'
    
    # Limpiar paquetes previos
    if build_dir.exists():
        shutil.rmtree(build_dir)
    if zip_path.exists():
        os.remove(zip_path)
    
    # Crear directorio de compilación
    package_dir.mkdir(parents=True, exist_ok=True)
    
    # Buscar el directorio site-packages (multiplataforma)
    site_packages = None
    for path in venv_site_packages.rglob('site-packages'):
        site_packages = path
        break
    
    if not site_packages or not site_packages.exists():
        print("Error: No se pudo encontrar site-packages. Asegúrate de haber ejecutado 'uv init' y 'uv add' para las dependencias.")
        sys.exit(1)
    
    print(f"Copiando dependencias desde {site_packages}...")
    # Copiar todas las dependencias al directorio del paquete
    for item in site_packages.iterdir():
        if item.name.endswith('.dist-info') or item.name == '__pycache__':
            continue
        if item.is_dir():
            shutil.copytree(item, package_dir / item.name, dirs_exist_ok=True)
        else:
            shutil.copy2(item, package_dir)
    
    # Copiar el código de la función Lambda
    print("Copiando código de la función Lambda...")
    
    # Copiar los handlers de Lambda de S3 Vectors
    if (current_dir / 'ingest_s3vectors.py').exists():
        shutil.copy(current_dir / 'ingest_s3vectors.py', package_dir)
    if (current_dir / 'search_s3vectors.py').exists():
        shutil.copy(current_dir / 'search_s3vectors.py', package_dir)
    
    # Crear archivo ZIP
    print("Creando paquete de despliegue...")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(package_dir):
            # Saltar directorios __pycache__
            dirs[:] = [d for d in dirs if d != '__pycache__']
            for file in files:
                if file.endswith('.pyc'):
                    continue
                file_path = Path(root) / file
                arcname = file_path.relative_to(package_dir)
                zipf.write(file_path, arcname)
    
    # Limpiar el directorio de compilación
    shutil.rmtree(build_dir)
    
    # Obtener el tamaño del archivo
    size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"\n✅ Paquete de despliegue creado: {zip_path}")
    print(f"   Tamaño: {size_mb:.2f} MB")
    
    if size_mb > 50:
        print("⚠️  Advertencia: El paquete supera los 50MB. Considera utilizar Lambda Layers.")
    
    return str(zip_path)


if __name__ == '__main__':
    create_deployment_package()