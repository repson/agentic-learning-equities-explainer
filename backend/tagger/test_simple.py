#!/usr/bin/env python3
"""
Test simple para el agente Tagger
"""

import asyncio
import json
from dotenv import load_dotenv

load_dotenv(override=True)

from lambda_handler import lambda_handler

def test_tagger():
    """Prueba el agente tagger con instrumentos desconocidos"""
    
    test_event = {
        "instruments": [
            {"symbol": "VTI", "name": "Vanguard Total Stock Market ETF"}
        ]
    }
    
    print("Probando el agente Tagger...")
    print("=" * 60)
    
    result = lambda_handler(test_event, None)
    
    print(f"Código de estado: {result['statusCode']}")
    
    if result['statusCode'] == 200:
        body = json.loads(result['body'])
        print(f"Etiquetados: {body.get('tagged', 0)} instrumentos")
        print(f"Actualizados: {body.get('updated', [])}")
        if body.get('classifications'):
            for c in body['classifications']:
                print(f"  {c['symbol']}: {c['type']}")
    else:
        print(f"Error: {result['body']}")
    
    print("=" * 60)

if __name__ == "__main__":
    test_tagger()