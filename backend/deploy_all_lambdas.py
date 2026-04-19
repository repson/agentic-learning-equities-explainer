#!/usr/bin/env python3
"""
Despliega todas las funciones Lambda de la Parte 6 en AWS usando Terraform.
Este script asegura que las funciones Lambda se actualicen correctamente mediante:
1. Empaquetar opcionalmente las funciones Lambda
2. "Taint" de los recursos Lambda en Terraform para forzar su recreación
3. Ejecutar terraform apply para desplegar con el código más reciente

Uso:
    cd backend
    uv run deploy_all_lambdas.py [--package]
    
Opciones:
    --package    Fuerza el empaquetado de todas las funciones Lambda antes del despliegue
"""

import boto3
import sys
import subprocess
import os
from pathlib import Path
from typing import List, Tuple

def taint_and_deploy_via_terraform() -> bool:
    """
    Despliega las funciones Lambda usando Terraform con recreación forzada.
    
    Returns:
        True si tiene éxito, False en caso contrario
    """
    # Cambiar al directorio de terraform
    terraform_dir = Path(__file__).parent.parent / "terraform" / "6_agents"
    if not terraform_dir.exists():
        print(f"❌ Directorio de Terraform no encontrado: {terraform_dir}")
        return False
    
    # Nombres de funciones Lambda a taint
    lambda_functions = ['planner', 'tagger', 'reporter', 'charter', 'retirement']
    
    print("📌 Paso 1: Realizando taint de funciones Lambda para forzar recreación...")
    print("-" * 50)
    
    # Taint de cada función Lambda
    for func in lambda_functions:
        print(f"   Realizando taint a aws_lambda_function.{func}...")
        result = subprocess.run(
            ['terraform', 'taint', f'aws_lambda_function.{func}'],
            cwd=terraform_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0 or "already" in result.stderr:
            print(f"      ✓ {func} marcada para recreación")
        elif "No such resource instance" in result.stderr:
            print(f"      ⚠️ {func} no existe (se creará)")
        else:
            print(f"      ⚠️ Advertencia: {result.stderr[:100]}")
    
    print()
    print("🚀 Paso 2: Ejecutando terraform apply...")
    print("-" * 50)
    
    # Ejecutar terraform apply
    result = subprocess.run(
        ['terraform', 'apply', '-auto-approve'],
        cwd=terraform_dir,
        capture_output=False,  # Mostrar salida directamente
        text=True
    )
    
    if result.returncode == 0:
        print()
        print("✅ ¡Despliegue de Terraform completado exitosamente!")
        return True
    else:
        print()
        print("❌ ¡El despliegue de Terraform falló!")
        return False

def package_lambda(service_name: str, service_dir: Path) -> bool:
    """
    Empaqueta una función Lambda usando package_docker.py.
    
    Args:
        service_name: Nombre del servicio (por ejemplo, 'planner')
        service_dir: Ruta al directorio del servicio
        
    Returns:
        True si tiene éxito, False en caso contrario
    """
    print(f"   📦 Empaquetando {service_name}...")
    
    package_script = service_dir / 'package_docker.py'
    if not package_script.exists():
        print(f"      ✗ package_docker.py no encontrado en {service_dir}")
        return False
    
    try:
        # Ejecutar uv run package_docker.py en el directorio del servicio
        result = subprocess.run(
            ['uv', 'run', 'package_docker.py'],
            cwd=service_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            # Verificar si se creó el zip
            zip_path = service_dir / f'{service_name}_lambda.zip'
            if zip_path.exists():
                size_mb = zip_path.stat().st_size / (1024 * 1024)
                print(f"      ✓ Paquete de {size_mb:.1f} MB creado")
                return True
            else:
                print(f"      ✗ Paquete no creado")
                return False
        else:
            print(f"      ✗ Falló el empaquetado: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"      ✗ Error al ejecutar package_docker.py: {e}")
        return False

def main():
    """Función principal de despliegue."""
    # Comprobar flag --package
    force_package = '--package' in sys.argv
    
    print("🎯 Desplegando funciones Lambda del Agente Alex (vía Terraform)")
    print("=" * 50)
    
    # Obtener el ID de cuenta AWS
    try:
        sts_client = boto3.client('sts')
        account_id = sts_client.get_caller_identity()['Account']
        region = boto3.Session().region_name
        print(f"Cuenta AWS: {account_id}")
        print(f"Región AWS: {region}")
    except Exception as e:
        print(f"❌ Error al obtener la información de la cuenta AWS: {e}")
        print("   Asegúrate de que tus credenciales de AWS están configuradas")
        sys.exit(1)
    
    print()
    
    # Definir funciones Lambda a comprobar/empaquetar
    backend_dir = Path(__file__).parent
    services = [
        ('planner', backend_dir / 'planner' / 'planner_lambda.zip'),
        ('tagger', backend_dir / 'tagger' / 'tagger_lambda.zip'),
        ('reporter', backend_dir / 'reporter' / 'reporter_lambda.zip'),
        ('charter', backend_dir / 'charter' / 'charter_lambda.zip'),
        ('retirement', backend_dir / 'retirement' / 'retirement_lambda.zip'),
    ]
    
    # Comprobar si existen paquetes y empaquetar opcionalmente
    print("📋 Comprobando paquetes de despliegue...")
    services_to_package = []
    
    for service_name, zip_path in services:
        service_dir = backend_dir / service_name
        
        if force_package:
            # Forzar el empaquetado de todos los servicios
            services_to_package.append((service_name, service_dir))
            print(f"   ⟳ {service_name}: Se volverá a empaquetar")
        elif zip_path.exists():
            size_mb = zip_path.stat().st_size / (1024 * 1024)
            print(f"   ✓ {service_name}: {size_mb:.1f} MB")
        else:
            print(f"   ✗ {service_name}: No encontrado")
            services_to_package.append((service_name, service_dir))
    
    # Empaquetar servicios faltantes o todos si se solicita
    if services_to_package:
        print()
        print("📦 Empaquetando funciones Lambda...")
        failed_packages = []
        
        for service_name, service_dir in services_to_package:
            if not package_lambda(service_name, service_dir):
                failed_packages.append(service_name)
        
        if failed_packages:
            print()
            print(f"❌ Falló el empaquetado de: {', '.join(failed_packages)}")
            print("   Asegúrate de que Docker esté corriendo y que exista package_docker.py")
            response = input("¿Continuar de todos modos? (y/N): ")
            if response.lower() != 'y':
                sys.exit(1)
    
    print()
    
    # Desplegar vía Terraform con recreación forzada
    if taint_and_deploy_via_terraform():
        print()
        print("🎉 ¡Todas las funciones Lambda se desplegaron exitosamente!")
        print()
        print("⚠️  IMPORTANTE: Las funciones Lambda fueron RECREADAS FORZADAMENTE")
        print("   Esto asegura que tu código más reciente está corriendo en AWS")
        print()
        print("Siguientes pasos:")
        print("   1. Prueba local: cd <servicio> && uv run test_simple.py")
        print("   2. Prueba de integración: cd backend && uv run test_full.py")
        print("   3. Monitorea los logs de CloudWatch para cada función")
        sys.exit(0)
    else:
        print()
        print("❌ ¡El despliegue falló!")
        print()
        print("💡 Consejos de resolución de problemas:")
        print("   1. Revisa la salida de terraform en busca de errores")
        print("   2. Asegúrate de que todos los paquetes existan (usa la bandera --package)")
        print("   3. Verifica credenciales y permisos de AWS")
        print("   4. Chequea el estado de terraform: cd terraform/6_agents && terraform plan")
        sys.exit(1)

if __name__ == "__main__":
    main()