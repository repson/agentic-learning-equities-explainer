#!/usr/bin/env python3
"""
Empaqueta la API de FastAPI para su despliegue en Lambda usando Docker.
Esto asegura la compatibilidad binaria con el entorno de ejecución de Lambda.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
import tempfile
import zipfile

def run_command(cmd, cwd=None):
    """Ejecuta un comando de shell y maneja los errores."""
    print(f"Ejecutando: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result.stdout

def main():
    # Obtener el directorio de la API
    api_dir = Path(__file__).parent.absolute()
    backend_dir = api_dir.parent
    project_root = backend_dir.parent

    print(f"Directorio de la API: {api_dir}")
    print(f"Directorio backend: {backend_dir}")

    # Verificar si Docker está corriendo
    try:
        run_command(["docker", "info"])
    except Exception as e:
        print("Error: Docker no está en funcionamiento o no está instalado")
        print("Por favor, asegúrese de que Docker Desktop esté en funcionamiento e intente de nuevo")
        sys.exit(1)

    # Crear directorio temporal para empaquetar
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        package_dir = temp_path / "package"
        package_dir.mkdir()

        print(f"Empaquetando en: {package_dir}")

        # Copiar el código de la API
        api_package = package_dir / "api"
        shutil.copytree(api_dir, api_package, ignore=shutil.ignore_patterns(
            "__pycache__", "*.pyc", ".env*", "*.zip", "package_docker.py", "test_*.py"
        ))

        # Copiar lambda_handler.py al nivel raíz para que Lambda lo encuentre
        shutil.copy2(api_dir / "lambda_handler.py", package_dir / "lambda_handler.py")

        # Copiar el paquete de base de datos
        database_src = backend_dir / "database" / "src"
        database_dst = package_dir / "src"
        if database_src.exists():
            shutil.copytree(database_src, database_dst, ignore=shutil.ignore_patterns(
                "__pycache__", "*.pyc"
            ))
            print(f"Paquete de base de datos copiado desde {database_src}")
        else:
            print(f"Advertencia: Paquete de base de datos no encontrado en {database_src}")

        # Crear requirements.txt desde pyproject.toml
        requirements_file = package_dir / "requirements.txt"
        with open(requirements_file, "w") as f:
            # Dependencias principales
            f.write("fastapi>=0.116.0\n")
            f.write("uvicorn>=0.35.0\n")
            f.write("mangum>=0.19.0\n")
            f.write("boto3>=1.26.0\n")
            f.write("fastapi-clerk-auth>=0.0.7\n")
            f.write("pydantic>=2.0.0\n")
            f.write("python-dotenv>=1.0.0\n")

        # Crear el Dockerfile
        dockerfile_content = """
FROM public.ecr.aws/lambda/python:3.13

# Copiar requirements e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -t /var/task

# Copiar el código de la aplicación
COPY . /var/task/

# Configurar el handler
CMD ["api.main.handler"]
"""

        dockerfile = package_dir / "Dockerfile"
        with open(dockerfile, "w") as f:
            f.write(dockerfile_content)

        # Construir imagen Docker para arquitectura x86_64 (entorno Lambda)
        print("Construyendo imagen Docker para arquitectura x86_64...")
        run_command([
            "docker", "build",
            "--platform", "linux/amd64",
            "-t", "alex-api-packager",
            "."
        ], cwd=package_dir)

        # Crear contenedor y extraer archivos
        print("Extrayendo paquete Lambda...")
        container_name = "alex-api-extract"

        # Eliminar el contenedor si existe
        run_command(["docker", "rm", "-f", container_name], cwd=package_dir)

        # Crear el contenedor
        run_command([
            "docker", "create",
            "--name", container_name,
            "alex-api-packager"
        ], cwd=package_dir)

        # Extraer contenido de /var/task
        extract_dir = temp_path / "lambda"
        extract_dir.mkdir()

        run_command([
            "docker", "cp",
            f"{container_name}:/var/task/.",
            str(extract_dir)
        ])

        # Limpiar contenedor
        run_command(["docker", "rm", "-f", container_name])

        # Crear el zip final
        zip_path = api_dir / "api_lambda.zip"
        print(f"Creando archivo zip: {zip_path}")

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(extract_dir):
                # Saltar directorios __pycache__
                dirs[:] = [d for d in dirs if d != '__pycache__']

                for file in files:
                    # Saltar archivos .pyc
                    if file.endswith('.pyc'):
                        continue

                    file_path = Path(root) / file
                    arcname = file_path.relative_to(extract_dir)
                    zipf.write(file_path, arcname)

        # Obtener tamaño de archivo
        size_mb = zip_path.stat().st_size / (1024 * 1024)
        print(f"✅ Paquete Lambda creado: {zip_path} ({size_mb:.2f} MB)")

        # Verificar el paquete
        print("\nContenido del paquete (primeros 20 archivos):")
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            files = zipf.namelist()[:20]
            for f in files:
                print(f"  - {f}")
            if len(zipf.namelist()) > 20:
                print(f"  ... y {len(zipf.namelist()) - 20} archivos más")

if __name__ == "__main__":
    main()