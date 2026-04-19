#!/usr/bin/env python3
"""Prueba de escalabilidad con múltiples usuarios simultáneos (Fase 6.6)"""

import asyncio
import os
import json
import uuid
import boto3
import time
from datetime import datetime
from dotenv import load_dotenv
import concurrent.futures

# Cargar variables de entorno
load_dotenv(override=True)

from src import Database

async def create_test_user(user_num: int, num_accounts: int, num_positions: int):
    """Crea un usuario de prueba con un número especificado de cuentas y posiciones"""
    db = Database()
    
    # ID de usuario de prueba
    test_user = f"scale_test_{user_num}_{uuid.uuid4().hex[:6]}"
    
    # Crear usuario
    db.users.create_user(
        clerk_user_id=test_user,
        display_name=f"Usuario de Prueba de Escala {user_num}",
        years_until_retirement=20 + user_num * 5,
        target_retirement_income=50000 + user_num * 10000
    )
    
    # Asegurarse de que existen los instrumentos
    instruments = ["SPY", "BND", "VTI", "VXUS", "QQQ", "IWM", "EFA", "AGG", "VNQ", "GLD"]
    for i, symbol in enumerate(instruments):
        existing = db.instruments.find_by_symbol(symbol)
        if not existing:
            db.instruments.create({
                "symbol": symbol,
                "name": f"ETF de Prueba {symbol}",
                "instrument_type": "etf",
                "current_price": 100.0 + i * 50,
                "allocation_asset_class": {"equity": 100.0} if i % 2 == 0 else {"fixed_income": 100.0},
                "allocation_regions": {"north_america": 100.0},
                "allocation_sectors": {"other": 100.0}
            }, returning='symbol')
    
    account_ids = []
    total_positions = 0
    
    # Crear cuentas (asegurar al menos 1 cuenta incluso si num_accounts es 0)
    accounts_to_create = max(num_accounts, 1)
    for acct_num in range(1, accounts_to_create + 1):
        account_id = db.accounts.create_account(
            clerk_user_id=test_user,
            account_name=f"Cuenta {acct_num}",
            account_purpose="prueba",
            cash_balance=1000.0 * acct_num
        )
        account_ids.append(account_id)
        
        # Agregar posiciones (distribuir entre las cuentas)
        if num_positions > 0 and accounts_to_create > 0:
            positions_for_account = num_positions // accounts_to_create + (1 if acct_num <= (num_positions % accounts_to_create) else 0)
            for i in range(positions_for_account):
                if total_positions >= num_positions:
                    break
                symbol = instruments[total_positions % len(instruments)]
                qty = 10.0 * (total_positions + 1)
                db.positions.add_position(account_id, symbol, qty)
                total_positions += 1
    
    # Crear job
    job_data = {
        'clerk_user_id': test_user,
        'job_type': 'portfolio_analysis',
        'status': 'pending',
        'request_payload': {"test": f"scale_user_{user_num}"}
    }
    job_id = db.jobs.create(job_data)
    
    return {
        "user_id": test_user,
        "job_id": job_id,
        "account_ids": account_ids,
        "num_accounts": num_accounts,
        "num_positions": total_positions,
        "user_num": user_num
    }

async def send_job_to_sqs(job_id: str):
    """Enviar un job a SQS"""
    sqs = boto3.client('sqs', region_name=os.getenv('DEFAULT_AWS_REGION', 'us-east-1'))
    
    # Obtener URL de la cola
    queue_name = 'alex-analysis-jobs'
    response = sqs.get_queue_url(QueueName=queue_name)
    queue_url = response['QueueUrl']
    
    # Enviar mensaje
    message = {
        'job_id': job_id,
        'timestamp': datetime.now().isoformat()
    }
    
    response = sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(message)
    )
    
    return response['MessageId']

async def monitor_job(job_id: str, timeout: int = 300):
    """Monitoriza un job hasta su finalización"""
    db = Database()
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        job = db.jobs.find_by_id(job_id)
        
        if job['status'] == 'completed':
            elapsed = int(time.time() - start_time)
            return {"job_id": job_id, "status": "completed", "elapsed": elapsed}
        elif job['status'] == 'failed':
            return {"job_id": job_id, "status": "failed", "error": job.get('error_message')}
        
        await asyncio.sleep(5)
    
    return {"job_id": job_id, "status": "timeout"}

async def run_scale_test():
    """Ejecuta la prueba de escalabilidad con múltiples usuarios"""
    print("=" * 60)
    print("FASE 6.6: PRUEBA DE ESCALABILIDAD")
    print("=" * 60)
    
    # Configuración de prueba - 3 usuarios con múltiples cuentas según se requiera
    test_configs = [
        {"user_num": 1, "num_accounts": 1, "num_positions": 0},  # Portafolio vacío (una cuenta)
        {"user_num": 2, "num_accounts": 1, "num_positions": 3},  # Portafolio pequeño (una cuenta)
        {"user_num": 3, "num_accounts": 2, "num_positions": 5},  # Portafolio mediano (varias cuentas)
        {"user_num": 4, "num_accounts": 3, "num_positions": 10}, # Portafolio grande (varias cuentas)
        {"user_num": 5, "num_accounts": 2, "num_positions": 7},  # Portafolio mixto (varias cuentas)
    ]
    
    all_users = []
    
    # Crear todos los usuarios de prueba
    print("\n📊 Creando usuarios de prueba...")
    for config in test_configs:
        user_data = await create_test_user(**config)
        all_users.append(user_data)
        print(f"  Usuario {config['user_num']}: {user_data['num_accounts']} cuentas, {user_data['num_positions']} posiciones")
    
    # Enviar todos los jobs a SQS concurrentemente
    print("\n🚀 Enviando jobs a SQS...")
    send_tasks = []
    for user in all_users:
        msg_id = await send_job_to_sqs(user['job_id'])
        print(f"  Usuario {user['user_num']}: Job {user['job_id'][:8]}... enviado")
    
    # Monitorizar todos los jobs concurrentemente
    print("\n⏳ Monitorizando jobs (máx 5 minutos)...")
    print("-" * 50)
    
    monitor_tasks = [monitor_job(user['job_id']) for user in all_users]
    results = await asyncio.gather(*monitor_tasks)
    
    # Mostrar resultados
    print("-" * 50)
    print("\n📋 RESULTADOS:")
    print("-" * 50)
    
    successful = 0
    failed = 0
    timed_out = 0
    total_time = 0
    
    for i, result in enumerate(results):
        user = all_users[i]
        status = result['status']
        
        if status == 'completed':
            successful += 1
            total_time += result['elapsed']
            print(f"✅ Usuario {user['user_num']}: Completado en {result['elapsed']}s")
        elif status == 'failed':
            failed += 1
            print(f"❌ Usuario {user['user_num']}: Falló - {result.get('error', 'Desconocido')}")
        else:
            timed_out += 1
            print(f"⏱️ Usuario {user['user_num']}: Tiempo agotado")
    
    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print(f"Usuarios totales: {len(all_users)}")
    print(f"Exitosos: {successful}")
    print(f"Fallidos: {failed}")
    print(f"Tiempo agotado: {timed_out}")
    if successful > 0:
        print(f"Tiempo promedio de finalización: {total_time/successful:.1f}s")
    
    # Verificar detalles de jobs
    print("\n📊 Resultados Detallados:")
    db = Database()
    for user in all_users:
        job = db.jobs.find_by_id(user['job_id'])
        if job['status'] == 'completed':
            report_size = 0
            if job.get('report_payload'):
                report_data = job['report_payload']
                if isinstance(report_data, dict):
                    report_size = len(report_data.get('content', ''))
                else:
                    report_size = len(str(report_data))
            
            charts_payload = job.get('charts_payload')
            num_charts = len(charts_payload) if charts_payload else 0
            has_retirement = job.get('retirement_payload') is not None
            
            print(f"  Usuario {user['user_num']}: Reporte {report_size:,} caracteres, {num_charts} gráficos, Retiro: {has_retirement}")
    
    # Limpieza
    print("\n🧹 Limpiando datos de prueba...")
    for user in all_users:
        # Eliminar posiciones
        for account_id in user['account_ids']:
            db.execute_raw(
                "DELETE FROM positions WHERE account_id = :account_id::uuid",
                [{"name": "account_id", "value": {"stringValue": account_id}}]
            )
        
        # Eliminar cuentas
        db.execute_raw(
            "DELETE FROM accounts WHERE clerk_user_id = :user_id",
            [{"name": "user_id", "value": {"stringValue": user['user_id']}}]
        )
        
        # Eliminar jobs
        db.execute_raw(
            "DELETE FROM jobs WHERE clerk_user_id = :user_id",
            [{"name": "user_id", "value": {"stringValue": user['user_id']}}]
        )
        
        # Eliminar usuario
        db.execute_raw(
            "DELETE FROM users WHERE clerk_user_id = :user_id",
            [{"name": "user_id", "value": {"stringValue": user['user_id']}}]
        )
    
    print("Limpieza completada")
    
    # Resultado final
    if successful == len(all_users):
        print("\n✅ FASE 6.6 PRUEBA APROBADA: Todos los usuarios procesados exitosamente")
        return True
    else:
        print(f"\n❌ FASE 6.6 PRUEBA FALLIDA: {failed + timed_out} usuarios no se completaron")
        return False

async def main():
    """Punto de entrada principal"""
    try:
        success = await run_scale_test()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR durante la prueba: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())