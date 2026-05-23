"""
Manejador Lambda del Orquestador de Planificador Financiero
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

from templates import ORCHESTRATOR_INSTRUCTIONS
from agent import create_agent, handle_missing_instruments, load_portfolio_summary
from market import update_instrument_prices
from observability import observe

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Inicializar base de datos
db = Database()


def log_structured_event(event: str, job_id: str, user_id: str = None, **details) -> None:
    """Emitir logs estructurados para observabilidad enterprise."""
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

@retry(
    retry=retry_if_exception_type(RateLimitError),
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    before_sleep=lambda retry_state: logger.info(f"Planificador: Límite de velocidad alcanzado, reintentando en {retry_state.next_action.sleep} segundos...")
)
async def run_orchestrator(job_id: str) -> None:
    """Ejecuta el agente orquestador para coordinar el análisis de portafolio."""
    start_time = datetime.now(timezone.utc)
    start_perf = time.perf_counter()
    user_id = None

    try:
        job = db.jobs.find_by_id(job_id)
        if not job:
            logger.error(f"Planificador: Trabajo {job_id} no encontrado")
            return

        user_id = job.get("clerk_user_id")
        log_structured_event("PLANNER_STARTED", job_id, user_id=user_id)

        # Actualizar estado del trabajo a en ejecución
        db.jobs.update_status(job_id, 'running')
        
        # Manejar instrumentos faltantes primero (pre-procesamiento sin agente)
        await asyncio.to_thread(handle_missing_instruments, job_id, db)

        # Actualizar precios de instrumentos después de etiquetar
        logger.info("Planificador: Actualizando precios de instrumentos desde datos de mercado")
        await asyncio.to_thread(update_instrument_prices, job_id, db)

        # Cargar resumen de portafolio (solo estadísticas, no datos completos)
        portfolio_summary = await asyncio.to_thread(load_portfolio_summary, job_id, db)

        for agent_name in ["reporter", "charter", "retirement"]:
            log_structured_event(
                "AGENT_INVOKED",
                job_id,
                user_id=user_id,
                agent=agent_name,
            )

        # Crear agente con herramientas y contexto
        model, tools, task, context = create_agent(job_id, portfolio_summary, db)
        model_used = os.getenv("BEDROCK_MODEL_ID", "unknown")
        
        # Ejecutar el orquestador
        with trace("Orquestador del Planificador"):
            from agent import PlannerContext
            agent = Agent[PlannerContext](
                name="Planificador Financiero",
                instructions=ORCHESTRATOR_INSTRUCTIONS,
                model=model,
                tools=tools
            )
            
            result = await Runner.run(
                agent,
                input=task,
                context=context,
                max_turns=20
            )

            _ = truncate_response(result.final_output)
            
            # Marcar trabajo como completado después de que finalicen todos los agentes
            db.jobs.update_status(job_id, "completed")
            duration_ms = int((time.perf_counter() - start_perf) * 1000)
            AuditLogger.log_ai_decision(
                agent_name="planner",
                job_id=job_id,
                input_data={
                    "task": task,
                    "portfolio_summary": portfolio_summary,
                    "invoked_agents": ["reporter", "charter", "retirement"],
                },
                output_data={
                    "status": "completed",
                    "message": "planner_orchestration_completed",
                },
                model_used=model_used,
                duration_ms=duration_ms,
            )
            end_time = datetime.now(timezone.utc)
            log_structured_event(
                "PLANNER_COMPLETED",
                job_id,
                user_id=user_id,
                status="success",
                duration_seconds=(end_time - start_time).total_seconds(),
            )
            logger.info(f"Planificador: Trabajo {job_id} completado exitosamente")

    except Exception as e:
        end_time = datetime.now(timezone.utc)
        log_structured_event(
            "PLANNER_COMPLETED",
            job_id,
            user_id=user_id,
            status="failed",
            error=str(e),
            duration_seconds=(end_time - start_time).total_seconds(),
        )
        logger.error(f"Planificador: Error en la orquestación: {e}", exc_info=True)
        db.jobs.update_status(job_id, 'failed', error_message=str(e))
        raise

def lambda_handler(event, context):
    """
    Manejador Lambda para orquestación disparada por SQS.

    Evento esperado desde SQS:
    {
        "Records": [
            {
                "body": "job_id"
            }
        ]
    }
    """
    # Envolver todo el manejador con contexto de observabilidad
    with observe():
        try:
            logger.info(f"Lambda del Planificador invocada con evento: {json.dumps(event)[:500]}")

            # Extraer job_id desde el mensaje SQS
            if 'Records' in event and len(event['Records']) > 0:
                # Mensaje SQS
                job_id = event['Records'][0]['body']
                if isinstance(job_id, str) and job_id.startswith('{'):
                    # El body podría ser JSON
                    try:
                        body = json.loads(job_id)
                        job_id = body.get('job_id', job_id)
                    except json.JSONDecodeError:
                        pass
            elif 'job_id' in event:
                # Invocación directa
                job_id = event['job_id']
            else:
                logger.error("No se encontró job_id en el evento")
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'No se proporcionó job_id'})
                }

            logger.info(f"Planificador: Iniciando orquestación para el trabajo {job_id}")

            # Ejecutar el orquestador
            asyncio.run(run_orchestrator(job_id))

            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'message': f'Análisis completado para el trabajo {job_id}'
                })
            }

        except Exception as e:
            logger.error(f"Planificador: Error en el manejador lambda: {e}", exc_info=True)
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'success': False,
                    'error': str(e)
                })
            }

# Para pruebas locales
if __name__ == "__main__":
    # Definir un usuario de prueba
    test_user_id = "test_user_planner_local"

    # Asegurarse de que el usuario de prueba exista antes de crear un trabajo
    from src.schemas import UserCreate, JobCreate
    
    user = db.users.find_by_clerk_id(test_user_id)
    if not user:
        print(f"Creando usuario de prueba: {test_user_id}")
        user_create = UserCreate(clerk_user_id=test_user_id, display_name="Usuario Planificador Prueba")
        db.users.create(user_create.model_dump(), returning='clerk_user_id')

    # Crear un trabajo de prueba
    print("Creando trabajo de prueba...")
    job_create = JobCreate(
        clerk_user_id=test_user_id,
        job_type='portfolio_analysis',
        request_payload={
            'analysis_type': 'comprehensive',
            'test': True
        }
    )
    
    job = db.jobs.create(job_create.model_dump())
    job_id = job
    
    print(f"Trabajo de prueba creado: {job_id}")
    
    # Probar el manejador
    test_event = {
        'job_id': job_id
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))
