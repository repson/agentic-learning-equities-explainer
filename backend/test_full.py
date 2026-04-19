#!/usr/bin/env python3
"""Prueba completa de extremo a extremo vía SQS para la plataforma Alex"""

import os
import json
import boto3
import time
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv(override=True)

from src import Database
from src.schemas import UserCreate, InstrumentCreate, AccountCreate, PositionCreate

def setup_test_data(db):
    """Asegura que el usuario y portafolio de prueba existan"""
    print("Configurando datos de prueba...")

    # Verificar/crear usuario de prueba
    test_user_id = 'test_user_001'
    user = db.users.find_by_clerk_id(test_user_id)
    if not user:
        user_data = UserCreate(
            clerk_user_id=test_user_id,
            display_name="Usuario de Prueba",
            years_to_retirement=25,
            target_allocation={'stocks': 70, 'bonds': 20, 'alternatives': 10}
        )
        db.users.create(user_data.model_dump())
        print(f"  ✓ Usuario de prueba creado: {test_user_id}")
    else:
        print(f"  ✓ Usuario de prueba existente: {test_user_id}")

    # Verificar/crear cuenta de prueba
    accounts = db.accounts.find_by_user(test_user_id)
    if not accounts:
        account_data = AccountCreate(
            clerk_user_id=test_user_id,
            account_name="Prueba 401(k)",
            account_type="401k",
            cash_balance=5000.00
        )
        account_id = db.accounts.create(account_data.model_dump())
        print(f"  ✓ Cuenta de prueba creada: Prueba 401(k)")

        # Agregar algunas posiciones
        positions = [
            {'symbol': 'SPY', 'quantity': 100},
            {'symbol': 'QQQ', 'quantity': 50},
            {'symbol': 'BND', 'quantity': 200},
            {'symbol': 'VTI', 'quantity': 75}
        ]

        for pos in positions:
            position_data = PositionCreate(
                account_id=account_id,
                symbol=pos['symbol'],
                quantity=pos['quantity']
            )
            db.positions.create(position_data.model_dump())
        print(f"  ✓ {len(positions)} posiciones creadas")
    else:
        print(f"  ✓ Cuenta de prueba existente con {len(db.positions.find_by_account(accounts[0]['id']))} posiciones")

    return test_user_id

def main():
    print("=" * 70)
    print("🎯 Prueba completa de extremo a extremo vía SQS")
    print("=" * 70)

    db = Database()
    sqs = boto3.client('sqs')

    # Configurar datos de prueba
    test_user_id = setup_test_data(db)

    # Crear tarea de análisis de prueba
    print("\nCreando tarea de análisis...")
    job_data = {
        'clerk_user_id': test_user_id,
        'job_type': 'portfolio_analysis',
        'status': 'pending',
        'request_payload': {
            'analysis_type': 'full',
            'requested_at': datetime.now(timezone.utc).isoformat(),
            'test_run': True,
            'include_retirement': True,
            'include_charts': True,
            'include_report': True
        }
    }

    job_id = db.jobs.create(job_data)
    print(f"  ✓ Tarea creada: {job_id}")

    # Obtener URL de la cola
    QUEUE_NAME = 'alex-analysis-jobs'
    response = sqs.list_queues(QueueNamePrefix=QUEUE_NAME)
    queue_url = None
    for url in response.get('QueueUrls', []):
        if QUEUE_NAME in url:
            queue_url = url
            break

    if not queue_url:
        print(f"  ❌ Cola {QUEUE_NAME} no encontrada")
        return 1

    print(f"  ✓ Cola encontrada: {QUEUE_NAME}")

    # Enviar mensaje a SQS
    print("\nLanzando análisis vía SQS...")
    response = sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps({'job_id': job_id})
    )
    print(f"  ✓ Mensaje enviado: {response['MessageId']}")

    # Monitorear progreso de la tarea
    print("\n⏳ Monitoreando progreso de la tarea...")
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

            if status == 'failed' and job.get('error_message'):
                print(f"       Error: {job.get('error_message')}")

        if status == 'completed':
            print("-" * 50)
            print("\n✅ ¡Tarea completada exitosamente!")
            print("\n📊 Resultados del análisis:")

            # Reporte
            if job.get('report_payload'):
                report_content = job['report_payload'].get('content', '')
                print(f"\n📝 Reporte generado:")
                print(f"   - Longitud: {len(report_content)} caracteres")
                print(f"   - Vista previa: {report_content[:200]}...")
            else:
                print("\n❌ Reporte no encontrado")

            # Gráficas
            if job.get('charts_payload'):
                charts = job['charts_payload']
                print(f"\n📊 Gráficas creadas: {len(charts)} visualizaciones")
                for chart_key, chart_data in charts.items():
                    if isinstance(chart_data, dict):
                        title = chart_data.get('title', 'Sin título')
                        chart_type = chart_data.get('type', 'desconocido')
                        data_points = len(chart_data.get('data', []))
                        print(f"   - {chart_key}: {title} ({chart_type}, {data_points} puntos de datos)")
            else:
                print("\n❌ No se encontraron gráficas")

            # Jubilación
            if job.get('retirement_payload'):
                retirement = job['retirement_payload']
                print(f"\n🎯 Análisis de jubilación:")
                if isinstance(retirement, dict):
                    if 'success_rate' in retirement:
                        print(f"   - Tasa de éxito: {retirement['success_rate']}%")
                    if 'projected_balance' in retirement:
                        print(f"   - Balance proyectado: ${retirement['projected_balance']:,.0f}")
                    if 'analysis' in retirement:
                        print(f"   - Longitud del análisis: {len(retirement['analysis'])} caracteres")
            else:
                print("\n❌ No se encontró análisis de jubilación")

            # Resumen
            if job.get('summary_payload'):
                summary = job['summary_payload']
                print(f"\n📋 Resumen:")
                if isinstance(summary, dict):
                    for key, value in summary.items():
                        if key != 'timestamp':
                            print(f"   - {key}: {value}")

            break
        elif status == 'failed':
            print("-" * 50)
            print(f"\n❌ La tarea falló")
            if job.get('error_message'):
                print(f"Detalles del error: {job['error_message']}")
            break

        time.sleep(2)
    else:
        print("-" * 50)
        print("\n❌ La tarea expiró después de 3 minutos")
        print(f"Estado final: {job['status']}")
        return 1

    print(f"\n📋 Detalles de la tarea:")
    print(f"   - ID de tarea: {job_id}")
    print(f"   - ID de usuario: {test_user_id}")
    print(f"   - Tiempo total: {int(time.time() - start_time)} segundos")

    return 0

if __name__ == "__main__":
    exit(main())