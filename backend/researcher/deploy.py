#!/usr/bin/env python3
"""
Despliega el servicio researcher en AWS App Runner
Script de despliegue multiplataforma para Mac/Windows/Linux
"""

import subprocess
import sys
import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv(override=True)


def run_command(cmd, capture_output=False, shell=False):
    """Ejecuta un comando y maneja errores."""
    try:
        result = subprocess.run(
            cmd, shell=shell, capture_output=capture_output, text=True, check=True
        )
        if capture_output:
            return result.stdout.strip()
        return None
    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar el comando: {e}")
        if e.stderr:
            print(f"Detalles del error: {e.stderr}")
        sys.exit(1)


def main():
    print("Servicio Alex Researcher - Despliegue Docker")
    print("===========================================")

    # Obtener el ID de cuenta de AWS
    print("\nObteniendo detalles de la cuenta AWS...")
    account_id = run_command(
        ["aws", "sts", "get-caller-identity", "--query", "Account", "--output", "text"],
        capture_output=True,
    )

    region = os.environ.get("DEFAULT_AWS_REGION")
    if not region:
        print("Error: DEFAULT_AWS_REGION no se encuentra en tu archivo .env.")
        sys.exit(1)

    ecr_repository = "alex-researcher"

    print(f"Cuenta AWS: {account_id}")
    print(f"Región: {region}")

    # Obtener la URL del repositorio ECR desde Terraform
    print("\nObteniendo URL del repositorio ECR...")
    terraform_dir = Path(__file__).parent.parent.parent / "terraform" / "4_researcher"
    original_dir = os.getcwd()

    try:
        os.chdir(terraform_dir)
        ecr_url = run_command(
            ["terraform", "output", "-raw", "ecr_repository_url"], capture_output=True
        )
    finally:
        os.chdir(original_dir)

    if not ecr_url:
        print("Error: Repositorio ECR no encontrado. Ejecuta 'terraform apply' primero.")
        sys.exit(1)

    print(f"Repositorio ECR: {ecr_url}")

    # Iniciar sesión en ECR
    print("\nIniciando sesión en ECR...")
    password = run_command(
        ["aws", "ecr", "get-login-password", "--region", region], capture_output=True
    )

    login_cmd = ["docker", "login", "--username", "AWS", "--password-stdin", ecr_url]
    login_process = subprocess.Popen(
        login_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    stdout, stderr = login_process.communicate(input=password)

    if login_process.returncode != 0:
        print(f"Error al iniciar sesión en ECR: {stderr}")
        sys.exit(1)

    print("¡Inicio de sesión exitoso!")

    # Generar un tag único usando timestamp
    import time

    timestamp = int(time.time())
    image_tag = f"deploy-{timestamp}"

    # Construir la imagen Docker
    print(f"\nConstruyendo imagen Docker para linux/amd64 con la etiqueta: {image_tag}")
    print("(Esto asegura compatibilidad con AWS App Runner)")
    run_command(
        [
            "docker",
            "build",
            "--platform",
            "linux/amd64",
            "-t",
            f"{ecr_repository}:{image_tag}",
            # Eliminado --no-cache para usar caching de capas Docker y acelerar builds
            ".",
        ]
    )

    # Etiquetar para ECR con tag único y latest
    print("\nEtiquetando imagen para ECR...")
    run_command(["docker", "tag", f"{ecr_repository}:{image_tag}", f"{ecr_url}:{image_tag}"])
    run_command(["docker", "tag", f"{ecr_repository}:{image_tag}", f"{ecr_url}:latest"])

    # Subir a ECR
    print("\nSubiendo imagen a ECR...")
    run_command(["docker", "push", f"{ecr_url}:{image_tag}"])
    run_command(["docker", "push", f"{ecr_url}:latest"])

    print("\n✅ ¡Imagen Docker subida exitosamente!")
    print(
        "\nSiguiente paso: Ejecuta 'terraform apply' en terraform/4_researcher para crear el servicio App Runner."
    )

    # Obtener el ARN del servicio App Runner
    print("\nObteniendo detalles del servicio App Runner...")
    try:
        services = run_command(
            [
                "aws",
                "apprunner",
                "list-services",
                "--region",
                region,
                "--query",
                "ServiceSummaryList[?ServiceName=='alex-researcher'].ServiceArn",
                "--output",
                "json",
            ],
            capture_output=True,
        )

        if services:
            service_arns = json.loads(services)
            if service_arns:
                service_arn = service_arns[0]
                print(f"Servicio encontrado: {service_arn}")

                # Obtener la configuración actual para preservar el rol de acceso
                print("\nObteniendo configuración actual del servicio...")
                service_details = run_command(
                    [
                        "aws",
                        "apprunner",
                        "describe-service",
                        "--service-arn",
                        service_arn,
                        "--region",
                        region,
                        "--query",
                        "Service.SourceConfiguration.AuthenticationConfiguration.AccessRoleArn",
                        "--output",
                        "text",
                    ],
                    capture_output=True,
                )

                # Actualizar el servicio para usar la nueva imagen con tag único
                print(f"\nActualizando servicio para usar la nueva imagen: {ecr_url}:{image_tag}")
                run_command(
                    [
                        "aws",
                        "apprunner",
                        "update-service",
                        "--service-arn",
                        service_arn,
                        "--region",
                        region,
                        "--source-configuration",
                        json.dumps(
                            {
                                "ImageRepository": {
                                    "ImageIdentifier": f"{ecr_url}:{image_tag}",
                                    "ImageConfiguration": {
                                        "Port": "8000",
                                        "RuntimeEnvironmentVariables": {
                                            "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY", ""),
                                            "ALEX_API_KEY": os.environ.get("ALEX_API_KEY", ""),
                                            "ALEX_API_ENDPOINT": os.environ.get(
                                                "ALEX_API_ENDPOINT", ""
                                            ),
                                        },
                                    },
                                    "ImageRepositoryType": "ECR",
                                },
                                "AuthenticationConfiguration": {"AccessRoleArn": service_details},
                                "AutoDeploymentsEnabled": False,
                            }
                        ),
                    ],
                    capture_output=True,
                )
                print("✅ ¡Servicio actualizado con la nueva imagen!")

                # Esperar a que el despliegue se complete
                print("\nEsperando a que se complete el despliegue (esto puede tardar 5-10 minutos)...")
                import time

                max_attempts = 120  # 10 minutos con intervalos de 5 segundos
                attempts = 0

                while attempts < max_attempts:
                    status = run_command(
                        [
                            "aws",
                            "apprunner",
                            "describe-service",
                            "--service-arn",
                            service_arn,
                            "--region",
                            region,
                            "--query",
                            "Service.Status",
                            "--output",
                            "text",
                        ],
                        capture_output=True,
                    )

                    # Eliminar espacios en blanco que puedan causar problemas de comparación
                    status = status.strip()

                    if status == "RUNNING":
                        print("\n✅ ¡Despliegue completado! El servicio está en ejecución.")

                        # Obtener y mostrar la URL del servicio
                        service_url = run_command(
                            [
                                "aws",
                                "apprunner",
                                "describe-service",
                                "--service-arn",
                                service_arn,
                                "--region",
                                region,
                                "--query",
                                "Service.ServiceUrl",
                                "--output",
                                "text",
                            ],
                            capture_output=True,
                        )

                        print(f"\n🚀 Tu servicio está disponible en:")
                        print(f"   https://{service_url}")
                        print(f"\nPrueba con:")
                        print(f"   curl https://{service_url}/health")
                        break
                    elif status == "OPERATION_IN_PROGRESS":
                        # Comprobar el estado de la operación para más detalles
                        operation_status = run_command(
                            [
                                "aws",
                                "apprunner",
                                "list-operations",
                                "--service-arn",
                                service_arn,
                                "--region",
                                region,
                                "--query",
                                "OperationSummaryList[0].Status",
                                "--output",
                                "text",
                            ],
                            capture_output=True,
                        ).strip()

                        if operation_status == "SUCCEEDED":
                            # La operación terminó pero aún puede no haberse actualizado el estado del servicio
                            print("\n⏳ Operación completada, comprobando el estado del servicio...")
                            time.sleep(2)
                            continue
                        elif operation_status == "FAILED":
                            print(f"\n❌ ¡El despliegue ha fallado!")
                            print("Consulta la Consola de AWS para más detalles del error.")
                            break
                        else:
                            print(".", end="", flush=True)
                            # Mostrar el progreso cada 30 segundos
                            if attempts > 0 and attempts % 6 == 0:
                                elapsed_minutes = (attempts * 5) / 60
                                print(
                                    f" ({elapsed_minutes:.1f} minutos transcurridos)", end="", flush=True
                                )
                            time.sleep(5)
                            attempts += 1
                    else:
                        print(f"\n⚠️ Estado inesperado: {status}")
                        print("Consulta la Consola de AWS para más detalles.")
                        break
                else:
                    print("\n⚠️ El despliegue está tardando más de lo esperado.")
                    print("Consulta el estado en la Consola de AWS.")
            else:
                print(
                    "\nServicio App Runner no encontrado. Puede que tengas que ejecutar 'terraform apply' primero."
                )
                print("\nPara desplegar manualmente:")
                print("  1. Ve a la Consola AWS > App Runner")
                print("  2. Selecciona el servicio 'alex-researcher'")
                print("  3. Haz clic en 'Deploy' para obtener la imagen más reciente")
    except Exception as e:
        print(f"\nNo se pudo iniciar el despliegue automáticamente: {e}")
        print("\nPara desplegar manualmente:")
        print("  1. Ve a la Consola AWS > App Runner")
        print("  2. Selecciona el servicio 'alex-researcher'")
        print("  3. Haz clic en 'Deploy' para obtener la imagen más reciente")


if __name__ == "__main__":
    main()
