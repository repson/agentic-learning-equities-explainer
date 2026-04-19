"""
Manejador Lambda del Orquestador de Planificador Financiero
"""

import os
import json
import asyncio
import logging
from typing import Dict, Any

from agents import Agent, Runner, trace
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from litellm.exceptions import RateLimitError

try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass

# Importar paquete de base de datos
from src import Database

from templates import ORCHESTRATOR_INSTRUCTIONS
from agent import create_agent, handle_missing_instruments, load_portfolio_summary
from market import update_instrument_prices
from observability import observe

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Inicializar base de datos
db = Database()

@retry(
    retry=retry_if_exception_type(RateLimitError),
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    before_sleep=lambda retry_state: logger.info(f"Planificador: Límite de velocidad alcanzado, reintentando en {retry_state.next_action.sleep} segundos...")
)
async def run_orchestrator(job_id: str) -> None:
    """Ejecuta el agente orquestador para coordinar el análisis de portafolio."""
    try:
        # Actualizar estado del trabajo a en ejecución
        db.jobs.update_status(job_id, 'running')
        
        # Manejar instrumentos faltantes primero (pre-procesamiento sin agente)
        await asyncio.to_thread(handle_missing_instruments, job_id, db)

        # Actualizar precios de instrumentos después de etiquetar
        logger.info("Planificador: Actualizando precios de instrumentos desde datos de mercado")
        await asyncio.to_thread(update_instrument_prices, job_id, db)

        # Cargar resumen de portafolio (solo estadísticas, no datos completos)
        portfolio_summary = await asyncio.to_thread(load_portfolio_summary, job_id, db)
        
        # Crear agente con herramientas y contexto
        model, tools, task, context = create_agent(job_id, portfolio_summary, db)
        
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
            
            # Marcar trabajo como completado después de que finalicen todos los agentes
            db.jobs.update_status(job_id, "completed")
            logger.info(f"Planificador: Trabajo {job_id} completado exitosamente")
            
    except Exception as e:
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