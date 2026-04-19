#!/usr/bin/env python3
"""
Destruye la infraestructura de Alex Financial Advisor Parte 7.
Este script:
1. Vacía el bucket de S3
2. Destruye la infraestructura con Terraform
3. Limpia los artefactos locales
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, cwd=None, check=True, capture_output=False):
    """Ejecuta un comando y opcionalmente captura la salida."""
    print(f"Ejecutando: {' '.join(cmd) if isinstance(cmd, list) else cmd}")

    if capture_output:
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, shell=isinstance(cmd, str))
        if check and result.returncode != 0:
            print(f"Error: {result.stderr}")
            return None
        return result.stdout.strip()
    else:
        result = subprocess.run(cmd, cwd=cwd, shell=isinstance(cmd, str))
        if check and result.returncode != 0:
            return False
        return True


def confirm_destruction():
    """Pide confirmación antes de destruir los recursos."""
    print("⚠️  ADVERTENCIA: ¡Esto destruirá toda la infraestructura de la Parte 7!")
    print("Esto incluye:")
    print("  - Distribución CloudFront")
    print("  - API Gateway")
    print("  - Función Lambda")
    print("  - Bucket S3 y todos sus contenidos")
    print("  - Roles y políticas IAM")
    print("")

    response = input("¿Estás seguro de que quieres continuar? Escribe 'yes' para confirmar: ")
    return response.lower() == 'yes'


def get_bucket_name():
    """Obtiene el nombre del bucket S3 desde la salida de Terraform."""
    terraform_dir = Path(__file__).parent.parent / "terraform" / "7_frontend"

    if not terraform_dir.exists():
        print(f"  ❌ Directorio de Terraform no encontrado: {terraform_dir}")
        return None

    # Obtener el bucket desde Terraform
    bucket_output = run_command(
        ["terraform", "output", "-raw", "s3_bucket_name"],
        cwd=terraform_dir,
        capture_output=True
    )

    return bucket_output if bucket_output else None


def empty_s3_bucket(bucket_name):
    """Vacía el bucket de S3 antes de la eliminación."""
    if not bucket_name:
        print("  ⚠️  No se proporcionó un nombre de bucket, omitiendo...")
        return

    print(f"\n🗑️  Vaciando el bucket S3: {bucket_name}")

    # Comprobar si el bucket existe
    exists = run_command(
        ["aws", "s3", "ls", f"s3://{bucket_name}"],
        capture_output=True,
        check=False
    )

    if not exists:
        print(f"  El bucket {bucket_name} no existe o ya está vacío")
        return

    # Elimina todos los objetos
    print(f"  Eliminando todos los objetos de {bucket_name}...")
    run_command([
        "aws", "s3", "rm",
        f"s3://{bucket_name}/",
        "--recursive"
    ])

    # Elimina todas las versiones (si el versionado está habilitado)
    print(f"  Eliminando todas las versiones de objetos...")
    run_command([
        "aws", "s3api", "delete-objects",
        "--bucket", bucket_name,
        "--delete", "$(aws s3api list-object-versions --bucket " + bucket_name + " --output json --query='{Objects: Versions[].{Key:Key,VersionId:VersionId}}')"
    ], check=False)

    print(f"  ✅ Bucket {bucket_name} vaciado")


def destroy_terraform():
    """Destruye la infraestructura con Terraform."""
    print("\n🏗️  Destruyendo infraestructura con Terraform...")

    terraform_dir = Path(__file__).parent.parent / "terraform" / "7_frontend"

    if not terraform_dir.exists():
        print(f"  ❌ Directorio de Terraform no encontrado: {terraform_dir}")
        return False

    # Comprobar si Terraform está inicializado
    if not (terraform_dir / ".terraform").exists():
        print("  ⚠️  Terraform no inicializado, nada que destruir")
        return True

    # Destruye la infraestructura
    print("  Ejecutando terraform destroy...")
    print("  Escribe 'yes' cuando se solicite para confirmar la destrucción.")

    success = run_command(["terraform", "destroy"], cwd=terraform_dir)

    if success:
        print("  ✅ Infraestructura destruida exitosamente")
    else:
        print("  ❌ Falló la destrucción de la infraestructura")
        print("  Puede que necesites limpiar los recursos manualmente en la Consola de AWS")

    return success


def clean_local_artifacts():
    """Limpia los artefactos de construcción locales."""
    print("\n🧹 Limpiando artefactos locales...")

    artifacts = [
        Path(__file__).parent.parent / "backend" / "api" / "api_lambda.zip",
        Path(__file__).parent.parent / "frontend" / "out",
        Path(__file__).parent.parent / "frontend" / ".next",
    ]

    for artifact in artifacts:
        if artifact.exists():
            if artifact.is_file():
                artifact.unlink()
                print(f"  Eliminado: {artifact}")
            else:
                import shutil
                shutil.rmtree(artifact)
                print(f"  Directorio eliminado: {artifact}")

    print("  ✅ Artefactos locales limpiados")


def main():
    """Función principal de destrucción."""
    print("💥 Alex Financial Advisor - Destrucción de Infraestructura Parte 7")
    print("=" * 60)

    # Confirmar destrucción
    if not confirm_destruction():
        print("\n❌ Destrucción cancelada")
        sys.exit(0)

    # Obtener nombre de bucket antes de destruir la infraestructura
    bucket_name = get_bucket_name()

    # Vacía el bucket S3 primero (requerido antes de que Terraform pueda eliminarlo)
    if bucket_name:
        empty_s3_bucket(bucket_name)

    # Destruye la infraestructura de Terraform
    destroy_terraform()

    # Limpia artefactos locales
    clean_local_artifacts()

    print("\n" + "=" * 60)
    print("✅ ¡Destrucción completa!")
    print("\nPara volver a desplegar, ejecuta:")
    print("  uv run scripts/deploy.py")


if __name__ == "__main__":
    main()