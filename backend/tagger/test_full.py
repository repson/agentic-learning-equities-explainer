#!/usr/bin/env python3
"""
Test completo del agente Tagger a través de Lambda
"""

import os
import json
import boto3
from dotenv import load_dotenv

load_dotenv(override=True)

from src import Database

def test_tagger_lambda():
    """Test del agente Tagger mediante invocación Lambda"""
    
    db = Database()
    lambda_client = boto3.client('lambda')
    
    # Instrumentos de prueba que necesitan etiquetado
    test_instruments = [
        {"symbol": "ARKK", "name": "ARK Innovation ETF"},
        {"symbol": "SOFI", "name": "SoFi Technologies Inc"},
        {"symbol": "TSLA", "name": "Tesla Inc"}
    ]
    
    print("Probando Tagger Lambda")
    print("=" * 60)
    print(f"Instrumentos a etiquetar: {[i['symbol'] for i in test_instruments]}")
    
    # Invocar Lambda
    try:
        response = lambda_client.invoke(
            FunctionName='alex-tagger',
            InvocationType='RequestResponse',
            Payload=json.dumps({'instruments': test_instruments})
        )
        
        result = json.loads(response['Payload'].read())
        print(f"\nRespuesta Lambda: {json.dumps(result, indent=2)}")
        
        # Comprobar base de datos para instrumentos actualizados
        print("\n✅ Comprobando base de datos para instrumentos etiquetados:")
        for inst in test_instruments:
            instrument = db.instruments.find_by_symbol(inst['symbol'])
            if instrument:
                if instrument.get('allocation_asset_class'):
                    print(f"  ✅ {inst['symbol']}: Etiquetado correctamente")
                    print(f"     Clase de activo: {instrument.get('allocation_asset_class')}")
                    print(f"     Regiones: {instrument.get('allocation_regions')}")
                else:
                    print(f"  ❌ {inst['symbol']}: No se encontraron asignaciones")
            else:
                print(f"  ⚠️  {inst['symbol']}: No encontrado en la base de datos")
                
    except Exception as e:
        print(f"Error al invocar Lambda: {e}")
    
    print("=" * 60)

if __name__ == "__main__":
    test_tagger_lambda()