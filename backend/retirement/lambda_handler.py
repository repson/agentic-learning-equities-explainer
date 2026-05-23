"""
Manejador Lambda del Agente Especialista en Jubilación
"""

import os
import json
import asyncio
import logging
from typing import Dict, Any
from datetime import datetime, timezone
import time

from agents import Agent, Runner, trace
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from litellm.exceptions import RateLimitError

try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass

# Importar paquete de base de datos
from src import Database, AuditLogger

from templates import RETIREMENT_INSTRUCTIONS
from agent import create_agent
from observability import observe

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def log_structured_event(event: str, job_id: str, user_id: str = None, **details) -> None:
    payload = {
        "event": event,
        "job_id": job_id,
        "user_id": user_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    payload.update(details)
    logger.info(json.dumps(payload))


def truncate_response(text: str, max_length: int = 50000) -> str:
    """Asegurar que las respuestas no excedan un tamano razonable."""
    if text and len(text) > max_length:
        logger.warning(f"Response truncated from {len(text)} to {max_length} characters")
        return text[:max_length] + "\n\n[Response truncated due to length]"
    return text

def get_user_preferences(job_id: str) -> Dict[str, Any]:
    """Cargar preferencias del usuario desde la base de datos."""
    try:
        db = Database()
        
        # Obtener el trabajo para encontrar el usuario
        job = db.jobs.find_by_id(job_id)
        if job and job.get('clerk_user_id'):
            # Obtener las preferencias del usuario
            user = db.users.find_by_clerk_id(job['clerk_user_id'])
            if user:
                return {
                    'years_until_retirement': user.get('years_until_retirement', 30),
                    'target_retirement_income': float(user.get('target_retirement_income', 80000)),
                    'current_age': 40  # Predeterminado por ahora
                }
    except Exception as e:
        logger.warning(f"No se pudieron cargar los datos del usuario: {e}. Usando valores predeterminados.")
    
    return {
        'years_until_retirement': 30,
        'target_retirement_income': 80000.0,
        'current_age': 40
    }

@retry(
    retry=retry_if_exception_type(RateLimitError),
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    before_sleep=lambda retry_state: logger.info(f"Jubilación: Se alcanzó el límite de tasa, reintentando en {retry_state.next_action.sleep} segundos...")
)
async def run_retirement_agent(job_id: str, portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
    """Ejecutar el agente especialista en jubilación."""
    start_time = time.perf_counter()
    job = Database().jobs.find_by_id(job_id)
    user_id = job.get("clerk_user_id") if job else None
    log_structured_event("RETIREMENT_STARTED", job_id, user_id=user_id)
    
    # Obtener preferencias del usuario
    user_preferences = get_user_preferences(job_id)
    
    # Inicializar base de datos
    db = Database()
    
    # Crear agente (simplificado - sin herramientas ni contexto)
    model, tools, task = create_agent(job_id, portfolio_data, user_preferences, db)
    model_used = os.getenv("BEDROCK_MODEL_ID", "unknown")
    
    # Ejecutar agente (simplificado - sin contexto)
    with trace("Agente de Jubilación"):
        agent = Agent(
            name="Especialista en Jubilación",
            instructions=RETIREMENT_INSTRUCTIONS,
            model=model,
            tools=tools  # Lista vacía por ahora
        )
        
        result = await Runner.run(
            agent,
            input=task,
            max_turns=20
        )
        
        # Guardar el análisis en la base de datos
        analysis_text = truncate_response(result.final_output)

        retirement_payload = {
            'analysis': analysis_text,
            'generated_at': datetime.utcnow().isoformat(),
            'agent': 'retirement'
        }
        
        success = db.jobs.update_retirement(job_id, retirement_payload)
        
        if not success:
            logger.error(f"No se pudo guardar el análisis de jubilación para el trabajo {job_id}")

        log_structured_event(
            "RETIREMENT_COMPLETED",
            job_id,
            user_id=user_id,
            status="success" if success else "failed",
            analysis_length=len(result.final_output) if result.final_output else 0,
        )

        duration_ms = int((time.perf_counter() - start_time) * 1000)
        AuditLogger.log_ai_decision(
            agent_name="retirement",
            job_id=job_id,
            input_data={
                "task": task,
                "user_preferences": user_preferences,
                "portfolio_accounts": len(portfolio_data.get("accounts", [])),
            },
            output_data={
                "success": success,
                "analysis_length": len(analysis_text) if analysis_text else 0,
                "message": "retirement_analysis_generated",
            },
            model_used=model_used,
            duration_ms=duration_ms,
        )
        
        return {
            'success': success,
            'message': 'Análisis de jubilación completado' if success else 'Análisis completado pero falló al guardar',
            'final_output': analysis_text
        }

def lambda_handler(event, context):
    """
    Manejador Lambda esperando job_id en el evento.

    Evento esperado:
    {
        "job_id": "uuid",
        "portfolio_data": {...}  # Opcional, se cargará desde la BD si no se proporciona
    }
    """
    # Envuelve todo el manejador con el contexto de observabilidad
    with observe():
        start_time = datetime.now(timezone.utc)
        job_id = None
        user_id = None
        try:
            logger.info(f"Lambda de Jubilación invocada con el evento: {json.dumps(event)[:500]}")

            # Analizar el evento
            if isinstance(event, str):
                event = json.loads(event)

            job_id = event.get('job_id')
            if not job_id:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'job_id es obligatorio'})
                }

            job = Database().jobs.find_by_id(job_id)
            if job:
                user_id = job.get("clerk_user_id")

            portfolio_data = event.get('portfolio_data')
            if not portfolio_data:
                # Intentar cargar desde la base de datos
                try:
                    import sys
                    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
                    from src import Database

                    db = Database()
                    job = db.jobs.find_by_id(job_id)
                    if job:
                        portfolio_data = job.get('request_payload', {}).get('portfolio_data', {})
                    else:
                        return {
                            'statusCode': 404,
                            'body': json.dumps({'error': f'Trabajo {job_id} no encontrado'})
                        }
                except Exception as e:
                    logger.error(f"No se pudo cargar el portafolio desde la base de datos: {e}")
                    return {
                        'statusCode': 400,
                        'body': json.dumps({'error': 'No se proporcionaron datos del portafolio'})
                    }

            # Ejecutar el agente
            result = asyncio.run(run_retirement_agent(job_id, portfolio_data))

            end_time = datetime.now(timezone.utc)
            log_structured_event(
                "RETIREMENT_FINISHED",
                job_id,
                user_id=user_id,
                status="success",
                duration_seconds=(end_time - start_time).total_seconds(),
            )

            logger.info(f"Jubilación completada para el trabajo {job_id}")

            return {
                'statusCode': 200,
                'body': json.dumps(result)
            }

        except Exception as e:
            if job_id:
                end_time = datetime.now(timezone.utc)
                log_structured_event(
                    "RETIREMENT_FINISHED",
                    job_id,
                    user_id=user_id,
                    status="failed",
                    error=str(e),
                    duration_seconds=(end_time - start_time).total_seconds(),
                )
            logger.error(f"Error en jubilación: {e}", exc_info=True)
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'success': False,
                    'error': str(e)
                })
            }

# Para pruebas locales
if __name__ == "__main__":
    test_event = {
        "job_id": "test-retirement-123",
        "portfolio_data": {
            "accounts": [
                {
                    "name": "401(k)",
                    "type": "retirement",
                    "cash_balance": 10000,
                    "positions": [
                        {
                            "symbol": "SPY",
                            "quantity": 100,
                            "instrument": {
                                "name": "SPDR S&P 500 ETF",
                                "current_price": 450,
                                "allocation_asset_class": {"equity": 100}
                            }
                        },
                        {
                            "symbol": "BND",
                            "quantity": 100,
                            "instrument": {
                                "name": "Vanguard Total Bond Market ETF",
                                "current_price": 75,
                                "allocation_asset_class": {"fixed_income": 100}
                            }
                        }
                    ]
                }
            ]
        }
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))
