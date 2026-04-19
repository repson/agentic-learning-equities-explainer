#!/usr/bin/env python3
"""
Test completo para el agente Reporter vía Lambda
"""

import os
import json
import boto3
import time
from dotenv import load_dotenv

load_dotenv(override=True)

from src import Database
from src.schemas import JobCreate

def test_reporter_lambda():
    """Test del agente Reporter vía invocación Lambda"""
    
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
    
    print(f"Probando Lambda Reporter con el trabajo {job_id}")
    print("=" * 60)
    
    # Invocar Lambda
    try:
        response = lambda_client.invoke(
            FunctionName='alex-reporter',
            InvocationType='RequestResponse',
            Payload=json.dumps({'job_id': job_id})
        )
        
        result = json.loads(response['Payload'].read())
        print(f"Respuesta de Lambda: {json.dumps(result, indent=2)}")
        
        # Comprobar la base de datos por los resultados
        time.sleep(2)  # Dale un momento
        job = db.jobs.find_by_id(job_id)
        
        if job and job.get('report_payload'):
            print("\n✅ ¡Informe generado con éxito!")
            print(f"Vista previa del informe: {job['report_payload'][:500]}...")
        else:
            print("\n❌ No se encontró un informe en la base de datos")
            
    except Exception as e:
        print(f"Error al invocar Lambda: {e}")
    
    print("=" * 60)

if __name__ == "__main__":
    test_reporter_lambda()