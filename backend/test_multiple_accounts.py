#!/usr/bin/env python3
"""
Prueba que el sistema maneje correctamente usuarios con múltiples cuentas.
"""

import json
import time
import uuid
import boto3
import os
from decimal import Decimal
from dotenv import load_dotenv

from src import Database

# Cargar variables de entorno
load_dotenv(override=True)

def test_multiple_accounts():
    """Prueba el análisis para un usuario con múltiples cuentas"""
    
    print("=" * 70)
    print("🎯 Prueba de Múltiples Cuentas")
    print("=" * 70)
    
    # Inicializar base de datos
    db = Database()
    
    # Crear usuario de prueba
    test_user_id = f'test_multi_{uuid.uuid4().hex[:8]}'
    user_id = db.users.create_user(
        clerk_user_id=test_user_id,
        display_name='Usuario de Prueba Multi-Cuenta',
        years_until_retirement=25,
        target_retirement_income=Decimal('150000')
    )
    print(f'\n✅ Usuario de prueba creado: {test_user_id}')
    
    # Asegurar que existan los instrumentos
    instruments = [
        "SPY",
        "BND",
        "VTI",
        "VXUS",
        "QQQ",
        "IWM",
        "EFA",
        "AGG",
        "VNQ",
        "GLD",
        "VEA",
        "TSLA",
        "ARKK",
    ]
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
            print(f'✅ Instrumento creado: {symbol}')
    # Crear múltiples cuentas con diferentes portafolios
    accounts = []
    
    # Cuenta 1: Brokerage Imponible
    account1_id = db.accounts.create_account(
        clerk_user_id=test_user_id,
        account_name='Brokerage Imponible',
        account_purpose='taxable_brokerage',
        cash_balance=Decimal('5000.0')
    )
    accounts.append(account1_id)
    print(f'✅ Cuenta 1 creada: Brokerage Imponible')
    
    # Agregar posiciones a la cuenta 1
    positions1 = [
        ('SPY', 100),
        ('QQQ', 50),
        ('BND', 200)
    ]
    for symbol, quantity in positions1:
        sql = "INSERT INTO positions (account_id, symbol, quantity) VALUES (:account_id::uuid, :symbol, :quantity)"
        params = [
            {'name': 'account_id', 'value': {'stringValue': account1_id}},
            {'name': 'symbol', 'value': {'stringValue': symbol}},
            {'name': 'quantity', 'value': {'longValue': quantity}}
        ]
        db.client.execute(sql, params)
    print(f'  {len(positions1)} posiciones agregadas')
    
    # Cuenta 2: Roth IRA
    account2_id = db.accounts.create_account(
        clerk_user_id=test_user_id,
        account_name='Roth IRA',
        account_purpose='roth_ira',
        cash_balance=Decimal('2000.0')
    )
    accounts.append(account2_id)
    print(f'✅ Cuenta 2 creada: Roth IRA')
    
    # Agregar posiciones a la cuenta 2
    positions2 = [
        ('VTI', 75),
        ('VXUS', 50),
        ('GLD', 25)
    ]
    for symbol, quantity in positions2:
        sql = "INSERT INTO positions (account_id, symbol, quantity) VALUES (:account_id::uuid, :symbol, :quantity)"
        params = [
            {'name': 'account_id', 'value': {'stringValue': account2_id}},
            {'name': 'symbol', 'value': {'stringValue': symbol}},
            {'name': 'quantity', 'value': {'longValue': quantity}}
        ]
        db.client.execute(sql, params)
    print(f'  {len(positions2)} posiciones agregadas')
    
    # Cuenta 3: 401(k)
    account3_id = db.accounts.create_account(
        clerk_user_id=test_user_id,
        account_name='401(k)',
        account_purpose='401k',
        cash_balance=Decimal('10000.0')
    )
    accounts.append(account3_id)
    print(f'✅ Cuenta 3 creada: 401(k)')
    
    # Agregar posiciones a la cuenta 3
    positions3 = [
        ('VEA', 150),
        ('TSLA', 10),
        ('ARKK', 50),
        ('BND', 300)
    ]
    for symbol, quantity in positions3:
        sql = "INSERT INTO positions (account_id, symbol, quantity) VALUES (:account_id::uuid, :symbol, :quantity)"
        params = [
            {'name': 'account_id', 'value': {'stringValue': account3_id}},
            {'name': 'symbol', 'value': {'stringValue': symbol}},
            {'name': 'quantity', 'value': {'longValue': quantity}}
        ]
        db.client.execute(sql, params)
    print(f'  {len(positions3)} posiciones agregadas')
    
    print(f'\n📊 Total: 3 cuentas, {len(positions1) + len(positions2) + len(positions3)} posiciones')
    
    # Crear un job
    job_id = db.jobs.create_job(test_user_id, "portfolio_analysis")
    print(f'\n🚀 Job creado: {job_id}')
    
    # Lanzar análisis vía SQS
    """Enviar un job a SQS"""
    sqs = boto3.client('sqs', region_name=os.getenv('DEFAULT_AWS_REGION', 'us-east-1'))
    
    # Obtener la URL de la cola
    queue_name = 'alex-analysis-jobs'
    response = sqs.get_queue_url(QueueName=queue_name)
    queue_url = response['QueueUrl']

    # sqs = boto3.client('sqs', region_name='ap-southeast-2')
    # queue_url = 'https://sqs.ap-southeast-2.amazonaws.com/596644540428/alex-analysis-jobs'
    
    message = sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps({'job_id': job_id})
    )
    print(f'📤 Mensaje enviado a SQS: {message["MessageId"]}')
    
    print('\n⏳ Monitoreando el progreso del job...')
    print('-' * 50)
    
    # Monitorear job
    start_time = time.time()
    for i in range(90):  # Máximo 3 minutos
        time.sleep(2)
        job_status = db.jobs.find_by_id(job_id)
        status = job_status.get('status', 'unknown') if job_status else 'unknown'
        elapsed = int(time.time() - start_time)
        print(f'[{elapsed:3}s] Estado: {status}')
        if status in ['completed', 'failed']:
            break
    
    print('-' * 50)
    
    # Revisar resultados
    success = status == 'completed'
    
    if success:
        print('\n✅ ¡Job completado exitosamente!')
        
        # Revisar que todas las cuentas fueron analizadas
        print('\n📋 RESULTADOS DEL ANÁLISIS:')
        
        if job_status.get('summary_payload'):
            summary = job_status['summary_payload']
            print(f'\n🎯 Resumen:')
            print(f'  {summary.get("summary", "N/A")[:300]}...')
            
            # Revisar que hallazgos clave incluyen múltiples cuentas
            findings = summary.get('key_findings', [])
            if findings:
                print(f'\n📊 Hallazgos clave ({len(findings)}):')
                for finding in findings[:3]:
                    print(f'  • {finding}')
        
        if job_status.get('report_payload'):
            report = job_status['report_payload']
            content = report.get('content', '')
            # Verificar que el reporte mencione las 3 cuentas
            accounts_mentioned = all([
                'Taxable Brokerage' in content or 'taxable' in content.lower(),
                'Roth IRA' in content or 'roth' in content.lower(),
                '401(k)' in content or '401k' in content.lower()
            ])
            print(f'\n📝 Reporte:')
            print(f'  Longitud: {len(content)} caracteres')
            print(f'  ¿Todas las cuentas analizadas?: {"✅ SÍ" if accounts_mentioned else "❌ NO"}')
            
            if not accounts_mentioned:
                print('  ⚠️  Advertencia: No todas las cuentas aparecen en el reporte')
        
        if job_status.get('charts_payload'):
            charts = job_status['charts_payload']
            print(f'\n📊 Gráficas: {len(charts)} visualizaciones creadas')
            
            # Verificar si hay gráficas relacionadas a cuentas
            has_account_chart = any('account' in str(chart).lower() for chart in charts.values())
            print(f'  ¿Gráfica de distribución de cuentas?: {"✅ SÍ" if has_account_chart else "❌ NO"}')
        
        if job_status.get('retirement_payload'):
            print(f'\n🎯 Análisis de retiro: ✅ Generado')
    else:
        print(f'\n❌ Job falló con estado: {status}')
        if job_status.get('error'):
            print(f'Error: {job_status["error"]}')
    
    # Limpieza
    print(f'\n🧹 Limpiando datos de prueba...')
    try:
        # Eliminar job
        sql = "DELETE FROM jobs WHERE id = :job_id::uuid"
        params = [{'name': 'job_id', 'value': {'stringValue': job_id}}]
        db.client.execute(sql, params)
        
        # Eliminar posiciones
        for account_id in accounts:
            sql = "DELETE FROM positions WHERE account_id = :account_id::uuid"
            params = [{'name': 'account_id', 'value': {'stringValue': account_id}}]
            db.client.execute(sql, params)
        
        # Eliminar cuentas
        sql = "DELETE FROM accounts WHERE clerk_user_id = :user_id"
        params = [{'name': 'user_id', 'value': {'stringValue': test_user_id}}]
        db.client.execute(sql, params)
        
        # Eliminar usuario
        sql = "DELETE FROM users WHERE clerk_user_id = :user_id"
        params = [{'name': 'user_id', 'value': {'stringValue': test_user_id}}]
        db.client.execute(sql, params)
        
        print('✅ Datos de prueba limpiados exitosamente')
    except Exception as e:
        print(f'⚠️  Advertencia: Fallo al limpiar datos de prueba: {e}')
    
    print('\n' + '=' * 70)
    print(f'✅ ¡Prueba de múltiples cuentas {"APROBADA" if success else "FALLÓ"}!')
    print('=' * 70)
    
    return success


if __name__ == '__main__':
    success = test_multiple_accounts()
    exit(0 if success else 1)
