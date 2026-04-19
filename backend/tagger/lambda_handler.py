"""
InstrumentTagger Lambda Handler
Clasifica instrumentos financieros y actualiza la base de datos.
"""

import os
import json
import asyncio
import logging
from typing import List, Dict, Any

from src import Database
from src.schemas import InstrumentCreate
from agent import tag_instruments, classification_to_db_format
from observability import observe

# Configurar logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Inicializar base de datos
db = Database()

async def process_instruments(instruments: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Procesa y clasifica instrumentos de manera asíncrona.
    
    Args:
        instruments: Lista de instrumentos a clasificar
        
    Returns:
        Resultados del procesamiento
    """
    # Ejecutar la clasificación
    logger.info(f"Clasificando {len(instruments)} instrumentos")
    classifications = await tag_instruments(instruments)
    
    # Actualizar base de datos con clasificaciones
    updated = []
    errors = []
    
    for classification in classifications:
        try:
            # Convertir a formato de base de datos
            db_instrument = classification_to_db_format(classification)
            
            # Comprobar si el instrumento existe
            existing = db.instruments.find_by_symbol(classification.symbol)
            
            if existing:
                # Actualizar instrumento existente
                update_data = db_instrument.model_dump()
                # Eliminar el símbolo ya que es la clave
                del update_data['symbol']
                
                rows = db.client.update(
                    'instruments',
                    update_data,
                    "symbol = :symbol",
                    {'symbol': classification.symbol}
                )
                logger.info(f"Actualizado {classification.symbol} en la base de datos ({rows} filas)")
            else:
                # Crear nuevo instrumento
                db.instruments.create_instrument(db_instrument)
                logger.info(f"Creado {classification.symbol} en la base de datos")
            
            updated.append(classification.symbol)
            
        except Exception as e:
            logger.error(f"Error actualizando {classification.symbol}: {e}")
            errors.append({
                'symbol': classification.symbol,
                'error': str(e)
            })
    
    # Preparar la respuesta (convertir modelos Pydantic a diccionarios)
    return {
        'tagged': len(classifications),
        'updated': updated,
        'errors': errors,
        'classifications': [
            {
                'symbol': c.symbol,
                'name': c.name,
                'type': c.instrument_type,
                'current_price': c.current_price,
                'asset_class': c.allocation_asset_class.model_dump(),
                'regions': c.allocation_regions.model_dump(),
                'sectors': c.allocation_sectors.model_dump()
            }
            for c in classifications
        ]
    }

def lambda_handler(event, context):
    """
    Handler Lambda para el etiquetado de instrumentos.

    Formato esperado del evento:
    {
        "instruments": [
            {"symbol": "VTI", "name": "Vanguard Total Stock Market ETF"},
            ...
        ]
    }
    """
    # Envolver todo el handler en el contexto de observabilidad
    with observe():
        try:
            # Parsear el evento
            instruments = event.get('instruments', [])

            if not instruments:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'No se proporcionaron instrumentos'})
                }

            # Procesar todos los instrumentos en un único contexto asíncrono
            result = asyncio.run(process_instruments(instruments))

            return {
                'statusCode': 200,
                'body': json.dumps(result)
            }

        except Exception as e:
            logger.error(f"Error en lambda handler: {e}")
            return {
                'statusCode': 500,
                'body': json.dumps({'error': str(e)})
            }