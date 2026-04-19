#!/usr/bin/env python3
"""
Prueba completa para Tagger: empaquetar, desplegar y probar
"""

import os
import sys
import json
import time
import subprocess
import boto3
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(override=True)

from src import Database

class TaggerTest:
    """Clase de prueba que empaqueta, despliega y prueba el Lambda de tagger"""

    def __init__(self):
        self.lambda_client = boto3.client('lambda', region_name='us-east-1')
        self.db = Database()

    def package_tagger(self):
        """Empaqueta el Lambda de tagger usando Docker"""
        print("\n📦 Empaquetando Lambda Tagger...")
        print("=" * 60)

        try:
            # Ejecutar package_docker.py
            result = subprocess.run(
                ['uv', 'run', 'package_docker.py'],
                cwd=Path(__file__).parent,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                print(f"❌ Error al empaquetar: {result.stderr}")
                return False

            # Comprobar si se creó el archivo zip
            zip_path = Path(__file__).parent / 'tagger_lambda.zip'
            if zip_path.exists():
                size_mb = zip_path.stat().st_size / (1024 * 1024)
                print(f"✅ Paquete creado: {zip_path} ({size_mb:.1f} MB)")
                return True
            else:
                print("❌ Archivo de paquete no encontrado")
                return False

        except Exception as e:
            print(f"❌ Error al empaquetar: {e}")
            return False

    def deploy_tagger(self):
        """Despliega el Lambda tagger en AWS"""
        print("\n🚀 Desplegando Lambda Tagger...")
        print("=" * 60)

        try:
            # El paquete es demasiado grande para subir directamente, se debe usar S3
            s3_client = boto3.client('s3', region_name='us-east-1')

            # Usar el bucket existente de paquetes Lambda
            bucket_name = f"alex-lambda-packages-{boto3.client('sts').get_caller_identity()['Account']}"
            key = 'tagger/tagger_lambda.zip'

            print(f"Subiendo al bucket de S3: {bucket_name}")
            zip_path = Path(__file__).parent / 'tagger_lambda.zip'

            # Subir a S3
            with open(zip_path, 'rb') as f:
                s3_client.upload_fileobj(f, bucket_name, key)

            print(f"✅ Subido a S3: s3://{bucket_name}/{key}")

            # Actualizar el código de la función Lambda desde S3
            print("Actualizando la función Lambda desde S3...")
            response = self.lambda_client.update_function_code(
                FunctionName='alex-tagger',
                S3Bucket=bucket_name,
                S3Key=key
            )

            # Esperar a que Lambda se actualice
            print("Esperando a que Lambda esté lista...")
            waiter = self.lambda_client.get_waiter('function_updated')
            waiter.wait(FunctionName='alex-tagger')

            print(f"✅ Lambda desplegada con éxito")
            print(f"   Última modificación: {response['LastModified']}")
            print(f"   Tamaño del código: {response['CodeSize'] / (1024*1024):.1f} MB")
            return True

        except Exception as e:
            print(f"❌ Error al desplegar: {e}")
            return False

    def test_tagger(self):
        """Prueba el Lambda tagger desplegado"""
        print("\n🧪 Probando Lambda Tagger...")
        print("=" * 60)

        # Instrumentos de prueba - mezcla de ETFs y acciones
        test_instruments = [
            {"symbol": "ARKK", "name": "ARK Innovation ETF", "instrument_type": "etf"},
            {"symbol": "SOFI", "name": "SoFi Technologies Inc", "instrument_type": "stock"},
            {"symbol": "TSLA", "name": "Tesla Inc", "instrument_type": "stock"},
            {"symbol": "VTI", "name": "Vanguard Total Stock Market ETF", "instrument_type": "etf"}
        ]

        print(f"Probando con {len(test_instruments)} instrumentos:")
        for inst in test_instruments:
            print(f"  - {inst['symbol']}: {inst['name']}")

        try:
            # Invocar Lambda
            print("\nInvocando la función Lambda...")
            start_time = time.time()

            response = self.lambda_client.invoke(
                FunctionName='alex-tagger',
                InvocationType='RequestResponse',
                Payload=json.dumps({'instruments': test_instruments})
            )

            elapsed = time.time() - start_time

            # Parsear respuesta
            result = json.loads(response['Payload'].read())

            if response['StatusCode'] == 200:
                print(f"✅ Lambda ejecutada con éxito en {elapsed:.1f} segundos")

                # Parsear el body si es un string
                if isinstance(result.get('body'), str):
                    body = json.loads(result['body'])
                else:
                    body = result.get('body', result)

                print(f"\n📊 Resultados:")
                print(f"  Clasificado: {body.get('tagged', 0)} instrumentos")
                print(f"  Actualizado: {body.get('updated', [])}")
                if body.get('errors'):
                    print(f"  Errores: {body.get('errors')}")

                # Mostrar clasificaciones
                if body.get('classifications'):
                    print(f"\n📈 Clasificaciones:")
                    for cls in body['classifications']:
                        print(f"\n  {cls['symbol']} ({cls['type']}):")
                        print(f"    Clase de activo: {cls.get('asset_class', {})}")
                        print(f"    Regiones: {cls.get('regions', {})}")
                        print(f"    Sectores: {cls.get('sectors', {})}")

                # Verificar en la base de datos
                print(f"\n🔍 Verificando en la base de datos:")
                for inst in test_instruments:
                    db_inst = self.db.instruments.find_by_symbol(inst['symbol'])
                    if db_inst and db_inst.get('allocation_asset_class'):
                        print(f"  ✅ {inst['symbol']}: Tiene asignaciones en la base de datos")
                    else:
                        print(f"  ⚠️  {inst['symbol']}: Sin asignaciones en la base de datos")

            else:
                print(f"❌ Lambda falló con estado {response['StatusCode']}")
                print(f"   Respuesta: {result}")

        except Exception as e:
            print(f"❌ Error al probar Lambda: {e}")
            import traceback
            traceback.print_exc()

    def run_all(self):
        """Ejecuta la prueba completa: empaquetar, desplegar y probar"""
        print("\n" + "=" * 60)
        print("🎯 Prueba completa de Tagger: Empaquetar, Desplegar y Probar")
        print("=" * 60)

        # Paso 1: Empaquetar
        if not self.package_tagger():
            print("\n❌ Error al empaquetar, deteniendo la prueba")
            return False

        # Paso 2: Desplegar
        if not self.deploy_tagger():
            print("\n❌ Error al desplegar, deteniendo la prueba")
            return False

        # Dar tiempo a Lambda para estabilizarse después del despliegue
        print("\n⏳ Esperando 5 segundos para que Lambda se estabilice...")
        time.sleep(5)

        # Paso 3: Probar
        self.test_tagger()

        print("\n" + "=" * 60)
        print("✅ Prueba completa finalizada!")
        print("=" * 60)

        # Recordatorio sobre Langfuse
        print("\n💡 Consulta tu dashboard de Langfuse para trazas:")
        print("   https://us.cloud.langfuse.com")

        return True

def main():
    """Punto de entrada principal"""
    tester = TaggerTest()
    tester.run_all()

if __name__ == "__main__":
    main()