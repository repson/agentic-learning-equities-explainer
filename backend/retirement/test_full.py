#!/usr/bin/env python3
"""
Test completo del agente Retirement vía Lambda
"""

import os
import json
import boto3
import time
from dotenv import load_dotenv

load_dotenv(override=True)

from src import Database
from src.schemas import JobCreate

def test_retirement_lambda():
    """Prueba el agente Retirement invocando la Lambda"""
    
    db = Database()
    lambda_client = boto3.client('lambda')
    
    # Crear trabajo de prueba
    test_user_id = "test_user_001"
    
    job_create = JobCreate(
        clerk_user_id=test_user_id,
        job_type="portfolio_analysis",
        request_payload={"analysis_type": "test", "test": True}
    )
    job_id = db.jobs.create(job_create.model_dump())
    
    print(f"Probando Lambda Retirement con el trabajo {job_id}")
    print("=" * 60)
    
    # Invocar Lambda
    try:
        response = lambda_client.invoke(
            FunctionName='alex-retirement',
            InvocationType='RequestResponse',
            Payload=json.dumps({'job_id': job_id})
        )
        
        result = json.loads(response['Payload'].read())
        print(f"Respuesta de la Lambda: {json.dumps(result, indent=2)}")
        
        # Consultar la base de datos para ver los resultados
        time.sleep(2)  # Dale un momento
        job = db.jobs.find_by_id(job_id)
        
        if job and job.get('retirement_payload'):
            print("\n✅ ¡Análisis de jubilación generado correctamente!")
            print(f"Vista previa del análisis: {json.dumps(job['retirement_payload'], indent=2)[:500]}...")
        else:
            print("\n❌ No se encontró análisis de jubilación en la base de datos")
            
    except Exception as e:
        print(f"Error al invocar la Lambda: {e}")
    
    print("=" * 60)

if __name__ == "__main__":
    test_retirement_lambda()