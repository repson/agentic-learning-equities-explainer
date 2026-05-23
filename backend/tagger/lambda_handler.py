"""
InstrumentTagger Lambda Handler
Clasifica instrumentos financieros y actualiza la base de datos.
"""

import os
import json
import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime, timezone
import time

from src import Database, AuditLogger
from src.schemas import InstrumentCreate
from agent import tag_instruments, classification_to_db_format
from observability import observe

# Configurar logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Inicializar base de datos
db = Database()


def log_structured_event(event: str, job_id: str = None, user_id: str = None, **details) -> None:
    payload = {
        "event": event,
        "job_id": job_id,
        "user_id": user_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    payload.update(details)
    logger.info(json.dumps(payload))

async def process_instruments(
    instruments: List[Dict[str, str]], job_id: str = "N/A"
) -> Dict[str, Any]:
    """
    Procesa y clasifica instrumentos de manera asíncrona.
    
    Args:
        instruments: Lista de instrumentos a clasificar
        
    Returns:
        Resultados del procesamiento
    """
    start_time = time.perf_counter()
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
    result_payload = {
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

    model_used = os.getenv("BEDROCK_MODEL_ID", "unknown")
    duration_ms = int((time.perf_counter() - start_time) * 1000)
    AuditLogger.log_ai_decision(
        agent_name="tagger",
        job_id=job_id,
        input_data={"instrument_count": len(instruments), "symbols": [i.get("symbol") for i in instruments]},
        output_data={"tagged": result_payload["tagged"], "errors": len(errors)},
        model_used=model_used,
        duration_ms=duration_ms,
    )

    return result_payload

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
        start_time = datetime.now(timezone.utc)
        job_id = event.get("job_id") if isinstance(event, dict) else None
        user_id = None
        try:
            # Parsear el evento
            instruments = event.get('instruments', [])

            if job_id:
                job = db.jobs.find_by_id(job_id)
                if job:
                    user_id = job.get("clerk_user_id")

            log_structured_event(
                "TAGGER_STARTED",
                job_id=job_id,
                user_id=user_id,
                instrument_count=len(instruments),
            )

            if not instruments:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'No se proporcionaron instrumentos'})
                }

            # Procesar todos los instrumentos en un único contexto asíncrono
            result = asyncio.run(process_instruments(instruments, job_id=job_id or "N/A"))
            end_time = datetime.now(timezone.utc)
            log_structured_event(
                "TAGGER_COMPLETED",
                job_id=job_id,
                user_id=user_id,
                status="success",
                tagged=result.get("tagged", 0),
                errors=len(result.get("errors", [])),
                duration_seconds=(end_time - start_time).total_seconds(),
            )

            return {
                'statusCode': 200,
                'body': json.dumps(result)
            }

        except Exception as e:
            end_time = datetime.now(timezone.utc)
            log_structured_event(
                "TAGGER_COMPLETED",
                job_id=job_id,
                user_id=user_id,
                status="failed",
                error=str(e),
                duration_seconds=(end_time - start_time).total_seconds(),
            )
            logger.error(f"Error en lambda handler: {e}")
            return {
                'statusCode': 500,
                'body': json.dumps({'error': str(e)})
            }
