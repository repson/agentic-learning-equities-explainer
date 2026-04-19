#!/usr/bin/env python3
"""
Ejecuta una prueba completa de extremo a extremo de la orquestación del agente Alex.
Esto crea un trabajo de prueba y lo monitorea hasta su finalización.

Uso:
    cd backend/planner
    uv run run_full_test.py
"""

import os
import json
import boto3
import time
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

# Cargar entorno
load_dotenv(override=True)

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Importar base de datos
from src import Database

db = Database()
sqs = boto3.client('sqs')
sts = boto3.client('sts')

# Obtener configuración
QUEUE_NAME = os.getenv('SQS_QUEUE_NAME', 'alex-analysis-jobs')


def get_queue_url():
    """Obtener la URL de la cola SQS."""
    response = sqs.list_queues(QueueNamePrefix=QUEUE_NAME)
    queues = response.get('QueueUrls', [])
    
    for queue_url in queues:
        if QUEUE_NAME in queue_url:
            return queue_url
    
    raise ValueError(f"Queue {QUEUE_NAME} not found")


def main():
    """Ejecutar la prueba completa."""
    print("=" * 70)
    print("🎯 Orquestación del Agente Alex - Prueba Completa")
    print("=" * 70)
    
    # Mostrar información de AWS
    account_id = sts.get_caller_identity()['Account']
    region = boto3.Session().region_name
    print(f"Cuenta AWS: {account_id}")
    print(f"Región AWS: {region}")
    print(f"Región Bedrock: {os.getenv('BEDROCK_REGION', 'us-west-2')}")
    print(f"Modelo Bedrock: {os.getenv('BEDROCK_MODEL_ID', 'No definido')}")
    print()
    
    # Comprobar usuario de prueba
    print("📊 Verificando datos de prueba...")
    test_user_id = 'test_user_001'
    user = db.users.find_by_clerk_id(test_user_id)
    
    if not user:
        print("❌ Usuario de prueba no encontrado. Por favor ejecuta primero la configuración de la base de datos:")
        print("   cd ../database && uv run reset_db.py --with-test-data")
        return 1
    
    print(f"✓ Usuario de prueba: {user.get('display_name', test_user_id)}")
    
    # Comprobar cuentas y posiciones
    accounts = db.accounts.find_by_user(test_user_id)
    total_positions = 0
    for account in accounts:
        positions = db.positions.find_by_account(account['id'])
        total_positions += len(positions)
    
    print(f"✓ Portafolio: {len(accounts)} cuentas, {total_positions} posiciones")
    
    # Crear trabajo de prueba
    print("\n🚀 Creando trabajo de prueba...")
    job_data = {
        'clerk_user_id': test_user_id,
        'job_type': 'portfolio_analysis',
        'status': 'pending',
        'request_payload': {
            'analysis_type': 'full',
            'requested_at': datetime.now(timezone.utc).isoformat(),
            'test_run': True
        }
    }
    
    job_id = db.jobs.create(job_data)
    print(f"✓ Trabajo creado: {job_id}")
    
    # Enviar a SQS
    print("\n📤 Enviando trabajo a la cola SQS...")
    try:
        queue_url = get_queue_url()
        response = sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps({'job_id': job_id})
        )
        print(f"✓ Mensaje enviado: {response['MessageId']}")
    except Exception as e:
        print(f"❌ Error al enviar a SQS: {e}")
        return 1
    
    # Monitorear trabajo
    print("\n⏳ Monitoreando progreso del trabajo (tiempo máximo: 3 minutos)...")
    print("-" * 50)
    
    start_time = time.time()
    timeout = 180  # 3 minutos
    last_status = None
    
    while time.time() - start_time < timeout:
        job = db.jobs.find_by_id(job_id)
        status = job['status']
        
        if status != last_status:
            elapsed = int(time.time() - start_time)
            print(f"[{elapsed:3d}s] Estado: {status}")
            last_status = status
        
        if status == 'completed':
            print("-" * 50)
            print("✅ ¡Trabajo completado exitosamente!")
            break
        elif status == 'failed':
            print("-" * 50)
            print(f"❌ Trabajo fallido: {job.get('error_message', 'Error desconocido')}")
            return 1
        
        time.sleep(2)
    else:
        print("-" * 50)
        print("❌ El trabajo excedió el tiempo límite de 3 minutos")
        return 1
    
    # Mostrar resultados
    print("\n" + "=" * 70)
    print("📋 RESULTADOS DEL ANÁLISIS")
    print("=" * 70)
    
    # Resumen del orquestador
    if job.get('summary_payload'):
        print("\n🎯 Resumen del Orquestador:")
        summary = job['summary_payload']
        print(f"Resumen: {summary.get('summary', 'N/D')}")
        
        if summary.get('key_findings'):
            print("\nHallazgos Clave:")
            for finding in summary['key_findings']:
                print(f"  • {finding}")
        
        if summary.get('recommendations'):
            print("\nRecomendaciones:")
            for rec in summary['recommendations']:
                print(f"  • {rec}")
    
    # Análisis del informe
    if job.get('report_payload'):
        print("\n📝 Informe del Portafolio:")
        report = job['report_payload']
        analysis = report.get('analysis', '')
        print(f"  Longitud: {len(analysis)} caracteres")
        if analysis:
            preview = analysis[:300]
            if len(analysis) > 300:
                preview += "..."
            print(f"  Vista previa: {preview}")
    
    # Gráficas
    if job.get('charts_payload'):
        print(f"\n📊 Visualizaciones: {len(job['charts_payload'])} gráficas")
        for chart_key, chart_data in job['charts_payload'].items():
            print(f"  • {chart_key}: {chart_data.get('title', 'Sin título')}")
            if chart_data.get('data'):
                print(f"    Puntos de datos: {len(chart_data['data'])}")
    
    # Proyecciones de jubilación
    if job.get('retirement_payload'):
        print("\n🎯 Análisis de Jubilación:")
        ret = job['retirement_payload']
        print(f"  Tasa de éxito: {ret.get('success_rate', 'N/D')}%")
        print(f"  Valor proyectado: ${ret.get('projected_value', 0):,.0f}")
        print(f"  Años para la jubilación: {ret.get('years_to_retirement', 'N/D')}")
    
    print("\n" + "=" * 70)
    print("✅ ¡Prueba completa realizada exitosamente!")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    exit(main())