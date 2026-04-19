#!/usr/bin/env python3
"""
Test simple para el orquestador Planner
"""

import asyncio
import json
import os
import subprocess
from dotenv import load_dotenv

load_dotenv(override=True)

# Simula lambdas para pruebas
os.environ['MOCK_LAMBDAS'] = 'true'

from src import Database
from src.schemas import JobCreate

def setup_test_data():
    """Asegura que existan los datos de prueba y crea un job de prueba"""
    # Ejecuta reset_db con datos de prueba para asegurar que hay un usuario y portafolio de prueba
    print("Asegurando que existan los datos de prueba...")
    result = subprocess.run(
        ["uv", "run", "reset_db.py", "--with-test-data", "--skip-drop"],
        cwd="../database",
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"Advertencia: No se pudo asegurar los datos de prueba: {result.stderr}")
    
    db = Database()
    
    # El script reset_db crea test_user_001
    test_user_id = "test_user_001"
    
    # Verifica si el usuario existe
    user = db.users.find_by_clerk_id(test_user_id)
    if not user:
        raise ValueError(f"Usuario de prueba {test_user_id} no encontrado. Por favor ejecuta: cd ../database && uv run reset_db.py --with-test-data")
    
    # Crea job de prueba
    job_create = JobCreate(
        clerk_user_id=test_user_id,
        job_type="portfolio_analysis",
        request_payload={"analysis_type": "comprehensive", "test": True}
    )
    job_id = db.jobs.create(job_create.model_dump())
    
    return job_id

def test_planner():
    """Prueba el orquestador planner"""
    
    # Configura los datos de prueba
    job_id = setup_test_data()
    
    test_event = {
        "job_id": job_id
    }
    
    print("Probando el Orquestador Planner...")
    print(f"ID del Job: {job_id}")
    print("=" * 60)
    
    from lambda_handler import lambda_handler
    
    result = lambda_handler(test_event, None)
    
    print(f"Código de estado: {result['statusCode']}")
    
    if result['statusCode'] == 200:
        body = json.loads(result['body'])
        print(f"Éxito: {body.get('success', False)}")
        print(f"Mensaje: {body.get('message', 'N/A')}")
    else:
        print(f"Error: {result['body']}")
    
    print("=" * 60)

if __name__ == "__main__":
    test_planner()