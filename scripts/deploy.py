#!/usr/bin/env python3
"""
Despliega la infraestructura de Alex Financial Advisor Parte 7.
Este script:
1. Empaqueta la función Lambda
2. Despliega la infraestructura con Terraform para obtener la URL de la API
3. Construye el frontend de NextJS con la URL de la API de producción
4. Sube los archivos del frontend a S3
5. Invalida la caché de CloudFront

NOTA: Este script utiliza .env.production para el despliegue y NO modifica .env.local
"""

import subprocess
import sys
import os
import json
import time
from pathlib import Path


def run_command(cmd, cwd=None, check=True, capture_output=False, env=None):
    """Ejecuta un comando y opcionalmente captura su salida."""
    print(f"Ejecutando: {' '.join(cmd) if isinstance(cmd, list) else cmd}")

    if capture_output:
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, shell=isinstance(cmd, str), env=env)
        if check and result.returncode != 0:
            print(f"Error: {result.stderr}")
            sys.exit(1)
        return result.stdout.strip()
    else:
        result = subprocess.run(cmd, cwd=cwd, shell=isinstance(cmd, str), env=env)
        if check and result.returncode != 0:
            sys.exit(1)
        return None


def check_prerequisites():
    """Verifica que todas las herramientas requeridas estén instaladas."""
    print("🔍 Verificando prerequisitos...")

    # Verifica las herramientas requeridas
    tools = {
        "docker": "Docker es requerido para el empaquetado de Lambda",
        "terraform": "Terraform es requerido para el despliegue de infraestructura",
        "npm": "npm es requerido para construir el frontend",
        "aws": "AWS CLI es requerido para la sincronización con S3 y la invalidación de CloudFront"
    }

    for tool, message in tools.items():
        try:
            run_command([tool, "--version"], capture_output=True)
            print(f"  ✅ {tool} está instalado")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"  ❌ {message}")
            sys.exit(1)

    # Verifica si Docker está corriendo
    try:
        run_command(["docker", "info"], capture_output=True)
        print("  ✅ Docker está corriendo")
    except subprocess.CalledProcessError:
        print("  ❌ Docker no está corriendo. Por favor inicia Docker Desktop.")
        sys.exit(1)

    # Verifica credenciales de AWS
    try:
        run_command(["aws", "sts", "get-caller-identity"], capture_output=True)
        print("  ✅ Credenciales de AWS configuradas")
    except subprocess.CalledProcessError:
        print("  ❌ Credenciales de AWS no configuradas. Ejecuta 'aws configure'")
        sys.exit(1)


def package_lambda():
    """Empaqueta la función Lambda usando Docker."""
    print("\n📦 Empaquetando función Lambda...")

    api_dir = Path(__file__).parent.parent / "backend" / "api"

    if not api_dir.exists():
        print(f"  ❌ Directorio de API no encontrado: {api_dir}")
        sys.exit(1)

    # Ejecuta el script de empaquetado
    run_command(["uv", "run", "package_docker.py"], cwd=api_dir)

    # Verifica si se creó el paquete
    lambda_zip = api_dir / "api_lambda.zip"
    if not lambda_zip.exists():
        print(f"  ❌ Paquete Lambda no creado: {lambda_zip}")
        sys.exit(1)

    size_mb = lambda_zip.stat().st_size / (1024 * 1024)
    print(f"  ✅ Paquete Lambda creado: {lambda_zip} ({size_mb:.2f} MB)")


def build_frontend(api_url=None):
    """Construye el frontend de NextJS."""
    print("\n🎨 Construyendo el frontend...")

    frontend_dir = Path(__file__).parent.parent / "frontend"

    if not frontend_dir.exists():
        print(f"  ❌ Directorio del frontend no encontrado: {frontend_dir}")
        sys.exit(1)

    # Instala dependencias si es necesario
    node_modules = frontend_dir / "node_modules"
    if not node_modules.exists():
        print("  Instalando dependencias...")
        run_command(["npm", "install"], cwd=frontend_dir)

    # Si se proporciona la URL de la API, crea .env.production.local para sobrescribir .env.local
    if api_url:
        print(f"  Creando .env.production.local con la URL de la API: {api_url}")
        env_prod_local = frontend_dir / ".env.production.local"

        # Copia desde .env.production como base
        env_prod = frontend_dir / ".env.production"
        if env_prod.exists():
            with open(env_prod, "r") as f:
                lines = f.readlines()
        else:
            # Como alternativa usa .env.local si no existe .env.production
            env_local = frontend_dir / ".env.local"
            if env_local.exists():
                with open(env_local, "r") as f:
                    lines = f.readlines()
            else:
                lines = []

        # Actualiza la URL de la API
        api_line_found = False
        for i, line in enumerate(lines):
            if line.startswith("NEXT_PUBLIC_API_URL="):
                lines[i] = f"NEXT_PUBLIC_API_URL={api_url}\n"
                api_line_found = True
                break

        if not api_line_found:
            lines.append(f"\nNEXT_PUBLIC_API_URL={api_url}\n")

        # Escribe en .env.production.local (máxima prioridad para builds de producción)
        with open(env_prod_local, "w") as f:
            f.writelines(lines)
        print("  ✅ .env.production.local creado con la URL de la API")

    # Construye el frontend - NextJS usará automáticamente .env.production en builds de producción
    print("  Construyendo la app NextJS para producción...")
    # Establece NODE_ENV en producción para asegurar el uso de .env.production
    build_env = os.environ.copy()
    build_env["NODE_ENV"] = "production"
    run_command(["npm", "run", "build"], cwd=frontend_dir, env=build_env)

    # Verifica el build
    out_dir = frontend_dir / "out"
    if not out_dir.exists():
        print(f"  ❌ No se encontró la salida del build: {out_dir}")
        print("  Asegúrate de que next.config.ts tenga output: 'export'")
        sys.exit(1)

    print(f"  ✅ Frontend construido exitosamente")


def deploy_terraform():
    """Despliega infraestructura con Terraform."""
    print("\n🏗️  Desplegando infraestructura con Terraform...")

    terraform_dir = Path(__file__).parent.parent / "terraform" / "7_frontend"

    if not terraform_dir.exists():
        print(f"  ❌ Directorio de Terraform no encontrado: {terraform_dir}")
        sys.exit(1)

    # Inicializa Terraform si es necesario
    if not (terraform_dir / ".terraform").exists():
        print("  Inicializando Terraform...")
        run_command(["terraform", "init"], cwd=terraform_dir)

    # Planea el despliegue
    print("  Planeando el despliegue...")
    run_command(["terraform", "plan"], cwd=terraform_dir)

    # Aplica el despliegue
    print("\n  Aplicando el despliegue...")
    print("  Creando recursos AWS...")
    run_command(["terraform", "apply", "-auto-approve"], cwd=terraform_dir)

    # Obtén los outputs
    print("\n  Obteniendo salidas...")
    outputs = run_command(
        ["terraform", "output", "-json"],
        cwd=terraform_dir,
        capture_output=True
    )

    return json.loads(outputs)


def upload_frontend(bucket_name, cloudfront_id):
    """Sube los archivos del frontend a S3."""
    print(f"\n📤 Subiendo frontend al bucket S3: {bucket_name}")

    frontend_dir = Path(__file__).parent.parent / "frontend" / "out"

    if not frontend_dir.exists():
        print(f"  ❌ Build del frontend no encontrado: {frontend_dir}")
        sys.exit(1)

    # Primero, limpia el bucket
    print("  Limpiando el bucket S3...")
    run_command([
        "aws", "s3", "rm",
        f"s3://{bucket_name}/",
        "--recursive"
    ])

    # Sube archivos HTML con el tipo de contenido correcto y sin caché
    print("  Subiendo archivos HTML...")
    run_command([
        "aws", "s3", "cp",
        str(frontend_dir) + "/",
        f"s3://{bucket_name}/",
        "--recursive",
        "--exclude", "*",
        "--include", "*.html",
        "--content-type", "text/html",
        "--cache-control", "max-age=0,no-cache,no-store,must-revalidate"
    ])

    # Sube archivos CSS
    print("  Subiendo archivos CSS...")
    run_command([
        "aws", "s3", "cp",
        str(frontend_dir) + "/",
        f"s3://{bucket_name}/",
        "--recursive",
        "--exclude", "*",
        "--include", "*.css",
        "--content-type", "text/css",
        "--cache-control", "max-age=31536000,public"
    ])

    # Sube archivos JS
    print("  Subiendo archivos JavaScript...")
    run_command([
        "aws", "s3", "cp",
        str(frontend_dir) + "/",
        f"s3://{bucket_name}/",
        "--recursive",
        "--exclude", "*",
        "--include", "*.js",
        "--content-type", "application/javascript",
        "--cache-control", "max-age=31536000,public"
    ])

    # Sube archivos JSON
    print("  Subiendo archivos JSON...")
    run_command([
        "aws", "s3", "cp",
        str(frontend_dir) + "/",
        f"s3://{bucket_name}/",
        "--recursive",
        "--exclude", "*",
        "--include", "*.json",
        "--content-type", "application/json",
        "--cache-control", "max-age=31536000,public"
    ])

    # Sube imágenes
    for ext, content_type in [
        ("*.png", "image/png"),
        ("*.jpg", "image/jpeg"),
        ("*.jpeg", "image/jpeg"),
        ("*.gif", "image/gif"),
        ("*.svg", "image/svg+xml"),
        ("*.ico", "image/x-icon")
    ]:
        run_command([
            "aws", "s3", "cp",
            str(frontend_dir) + "/",
            f"s3://{bucket_name}/",
            "--recursive",
            "--exclude", "*",
            "--include", ext,
            "--content-type", content_type,
            "--cache-control", "max-age=31536000,public"
        ])

    # Sube cualquier archivo restante con tipo de contenido genérico
    print("  Subiendo archivos restantes...")
    run_command([
        "aws", "s3", "sync",
        str(frontend_dir) + "/",
        f"s3://{bucket_name}/",
        "--cache-control", "max-age=31536000,public"
    ])

    print(f"  ✅ Frontend subido exitosamente")

    # Invalida la caché de CloudFront
    print(f"\n🔄 Invalidando caché de CloudFront...")
    result = run_command([
        "aws", "cloudfront", "create-invalidation",
        "--distribution-id", cloudfront_id,
        "--paths", "/*"
    ], capture_output=True)

    print(f"  ✅ Invalidación de CloudFront creada")


def display_deployment_info(outputs):
    """Muestra información del despliegue sin modificar archivos env locales."""
    print("\n📝 Información del Despliegue")

    # Extrae valores de outputs
    api_url = outputs["api_gateway_url"]["value"]
    cloudfront_url = outputs["cloudfront_url"]["value"]

    print(f"\n  ✅ ¡Despliegue exitoso!")
    print(f"\n  URL de CloudFront: {cloudfront_url}")
    print(f"  URL de API Gateway: {api_url}")
    print(f"\n  Nota: Tu archivo local .env.local permanece sin cambios.")
    print(f"  El build de producción utiliza .env.production con la URL de la API de AWS.")


def main():
    """Función principal de despliegue."""
    print("🚀 Despliegue de Alex Financial Advisor - Parte 7")
    print("=" * 50)

    # Verifica prerequisitos
    check_prerequisites()

    # Empaqueta Lambda
    package_lambda()

    # Despliega infraestructura primero para obtener la URL de la API
    outputs = deploy_terraform()

    # Obtiene la URL de la API de los outputs de terraform
    api_url = outputs["api_gateway_url"]["value"]

    # Construye el frontend con la URL de la API de producción
    build_frontend(api_url)

    # Extrae el ID de distribución de CloudFront
    cloudfront_url = outputs["cloudfront_url"]["value"]
    # Extrae el ID de distribución desde la URL de CloudFront
    dist_id_output = run_command([
        "aws", "cloudfront", "list-distributions",
        "--query", f"DistributionList.Items[?DomainName=='{cloudfront_url.replace('https://', '')}'].Id",
        "--output", "text"
    ], capture_output=True)

    if not dist_id_output:
        print("  ⚠️  No se pudo encontrar el ID de la distribución de CloudFront")
        print("  Deberás invalidar la caché manualmente")
        cloudfront_id = None
    else:
        cloudfront_id = dist_id_output

    # Sube el frontend
    bucket_name = outputs["s3_bucket_name"]["value"]
    if cloudfront_id:
        upload_frontend(bucket_name, cloudfront_id)
    else:
        print("\n📤 Subiendo frontend a S3...")
        run_command([
            "aws", "s3", "sync",
            str(Path(__file__).parent.parent / "frontend" / "out") + "/",
            f"s3://{bucket_name}/",
            "--delete"
        ])

    # Muestra info del despliegue (ya no modifica .env.local)
    display_deployment_info(outputs)

    print("\n" + "=" * 50)
    print("✅ ¡Despliegue completado!")
    print(f"\n🌐 Tu aplicación está disponible en:")
    print(f"   {outputs['cloudfront_url']['value']}")
    print(f"\n📊 Monitorea tu función Lambda en:")
    print(f"   AWS Console > Lambda > {outputs['lambda_function_name']['value']}")
    print("\n⏳ Nota: La distribución de CloudFront puede tardar 5-10 minutos en propagarse completamente")


if __name__ == "__main__":
    main()