"""
Manejador Lambda del Agente Creador de Gráficos
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

# Importar el paquete de base de datos
from src import Database, AuditLogger

from templates import CHARTER_INSTRUCTIONS
from agent import create_agent, validate_chart_data
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

@retry(
    retry=retry_if_exception_type(RateLimitError),
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    before_sleep=lambda retry_state: logger.info(f"Charter: Se alcanzó el límite de velocidad, reintentando en {retry_state.next_action.sleep} segundos...")
)
async def run_charter_agent(job_id: str, portfolio_data: Dict[str, Any], db=None) -> Dict[str, Any]:
    """Ejecuta el agente charter para generar datos de visualización."""
    start_time = time.perf_counter()
    
    # Crear agente sin herramientas - la salida será JSON
    model, task = create_agent(job_id, portfolio_data, db)
    model_used = os.getenv("BEDROCK_MODEL_ID", "unknown")
    
    # Ejecutar el agente - sin herramientas, sin contexto
    with trace("Charter Agent"):
        agent = Agent(
            name="Chart Maker",
            instructions=CHARTER_INSTRUCTIONS,
            model=model
        )
        
        result = await Runner.run(
            agent,
            input=task,
            max_turns=5  # Reducido ya que esperamos una respuesta JSON de un solo disparo
        )
        
        # Extraer y parsear JSON de la salida
        output = truncate_response(result.final_output)
        logger.info(f"Charter: El agente completó, longitud de la salida: {len(output) if output else 0}")
        
        # Registrar la salida real para depuración
        if output:
            logger.info(f"Charter: Vista previa de la salida (primeros 1000 caracteres): {output[:1000]}")
        else:
            logger.warning("Charter: ¡El agente devolvió salida vacía!")
            # Verificar si hubo mensajes
            if hasattr(result, 'messages') and result.messages:
                logger.info(f"Charter: Número de mensajes: {len(result.messages)}")
                for i, msg in enumerate(result.messages):
                    logger.info(f"Charter: Mensaje {i}: {str(msg)[:500]}")
        
        # Parsear la salida JSON
        charts_data = None
        charts_saved = False
        
        if output:
            # Intentar encontrar JSON en la salida
            # Buscar las llaves de apertura y cierre del objeto JSON
            start_idx = output.find('{')
            end_idx = output.rfind('}')
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = output[start_idx:end_idx + 1]
                logger.info(f"Charter: Subcadena JSON extraída, longitud: {len(json_str)}")
                
                try:
                    is_valid, error_msg, parsed_data = validate_chart_data(json_str)
                    if not is_valid:
                        logger.error(f"Charter: salida inválida del agente para {job_id}: {error_msg}")
                        parsed_data = {"charts": []}
                    charts = parsed_data.get('charts', [])
                    logger.info(f"Charter: JSON parseado exitosamente, se encontraron {len(charts)} gráficos")
                    
                    if charts:
                        # Construir el charts_payload con keys de gráficos como claves de nivel superior
                        charts_data = {}
                        for chart in charts:
                            chart_key = chart.get('key', f"chart_{len(charts_data) + 1}")
                            # Eliminar la 'key' de los datos del gráfico ya que ahora es la clave del diccionario
                            chart_copy = {k: v for k, v in chart.items() if k != 'key'}
                            charts_data[chart_key] = chart_copy
                        
                        logger.info(f"Charter: charts_data creado con llaves: {list(charts_data.keys())}")
                        
                        # Guardar en la base de datos
                        if db and charts_data:
                            try:
                                success = db.jobs.update_charts(job_id, charts_data)
                                charts_saved = bool(success)
                                logger.info(f"Charter: Actualización de la base de datos devolvió: {success}")
                            except Exception as e:
                                logger.error(f"Charter: Error en base de datos: {e}")
                    else:
                        logger.warning("Charter: No se encontraron gráficos en el JSON parseado")
                        
                except json.JSONDecodeError as e:
                    logger.error(f"Charter: Error al parsear JSON: {e}")
                    logger.error(f"Charter: Cadena JSON intentada: {json_str[:500]}...")
            else:
                logger.error(f"Charter: No se encontró estructura JSON en la salida")
                logger.error(f"Charter: Vista previa de la salida: {output[:500]}...")
        
        result_payload = {
            'success': charts_saved,
            'message': f'Se generaron {len(charts_data) if charts_data else 0} gráficos' if charts_saved else 'No se pudo generar gráficos',
            'charts_generated': len(charts_data) if charts_data else 0,
            'chart_keys': list(charts_data.keys()) if charts_data else []
        }

        duration_ms = int((time.perf_counter() - start_time) * 1000)
        AuditLogger.log_ai_decision(
            agent_name="charter",
            job_id=job_id,
            input_data={
                "task": task,
                "portfolio_accounts": len(portfolio_data.get("accounts", [])),
            },
            output_data=result_payload,
            model_used=model_used,
            duration_ms=duration_ms,
        )

        return result_payload

def lambda_handler(event, context):
    """
    Manejador Lambda que espera job_id y portfolio_data en el evento.

    Evento esperado:
    {
        "job_id": "uuid",
        "portfolio_data": {...}
    }
    """
    # Envolver todo el manejador con contexto de observabilidad
    with observe():
        start_time = datetime.now(timezone.utc)
        user_id = None
        job_id = None
        try:
            logger.info(f"Charter Lambda invocado con llaves de evento: {list(event.keys()) if isinstance(event, dict) else 'no es un dict'}")

            # Parsear evento
            if isinstance(event, str):
                event = json.loads(event)

            job_id = event.get('job_id')
            if not job_id:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'job_id es requerido'})
                }

            # Inicializar base de datos primero
            db = Database()

            portfolio_data = event.get('portfolio_data')
            if not portfolio_data:
                # Cargar los datos de portafolio desde la base de datos (igual que Reporter)
                logger.info(f"Charter: Cargando datos de portafolio para el job {job_id}")
                try:
                    job = db.jobs.find_by_id(job_id)
                    if job:
                        user_id = job['clerk_user_id']
                        user = db.users.find_by_clerk_id(user_id)
                        accounts = db.accounts.find_by_user(user_id)

                        portfolio_data = {
                            'user_id': user_id,
                            'job_id': job_id,
                            'years_until_retirement': user.get('years_until_retirement', 30) if user else 30,
                            'accounts': []
                        }

                        for account in accounts:
                            account_data = {
                                'id': account['id'],
                                'name': account['account_name'],
                                'type': account.get('account_type', 'investment'),
                                'cash_balance': float(account.get('cash_balance', 0)),
                                'positions': []
                            }

                            positions = db.positions.find_by_account(account['id'])
                            for position in positions:
                                instrument = db.instruments.find_by_symbol(position['symbol'])
                                if instrument:
                                    account_data['positions'].append({
                                        'symbol': position['symbol'],
                                        'quantity': float(position['quantity']),
                                        'instrument': instrument
                                    })

                            portfolio_data['accounts'].append(account_data)

                        logger.info(f"Charter: {len(portfolio_data['accounts'])} cuentas cargadas con posiciones")
                    else:
                        logger.error(f"Charter: No se encontró el job {job_id}")
                        return {
                            'statusCode': 404,
                            'body': json.dumps({'error': 'No se encontró el job'})
                        }
                except Exception as e:
                    logger.error(f"Charter: Error al cargar los datos del portafolio: {e}")
                    return {
                        'statusCode': 500,
                        'body': json.dumps({'error': f'No se pudo cargar los datos del portafolio: {str(e)}'})
                    }

            if not user_id:
                job = db.jobs.find_by_id(job_id)
                if job:
                    user_id = job.get('clerk_user_id')

            log_structured_event("CHARTER_STARTED", job_id, user_id=user_id)

            logger.info(f"Charter: Procesando job {job_id}")

            # Ejecutar el agente
            result = asyncio.run(run_charter_agent(job_id, portfolio_data, db))

            end_time = datetime.now(timezone.utc)
            log_structured_event(
                "CHARTER_COMPLETED",
                job_id,
                user_id=user_id,
                status="success",
                charts_generated=result.get('charts_generated', 0),
                duration_seconds=(end_time - start_time).total_seconds(),
            )

            logger.info(f"Charter completado para el job {job_id}: {result}")

            return {
                'statusCode': 200,
                'body': json.dumps(result)
            }

        except Exception as e:
            if job_id:
                end_time = datetime.now(timezone.utc)
                log_structured_event(
                    "CHARTER_COMPLETED",
                    job_id,
                    user_id=user_id,
                    status="failed",
                    error=str(e),
                    duration_seconds=(end_time - start_time).total_seconds(),
                )
            logger.error(f"Error en charter: {e}", exc_info=True)
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
        "job_id": "550e8400-e29b-41d4-a716-446655440001",
        "portfolio_data": {
            "accounts": [
                {
                    "id": "acc1",
                    "name": "401(k)",
                    "type": "401k",
                    "cash_balance": 5000,
                    "positions": [
                        {
                            "symbol": "SPY",
                            "quantity": 100,
                            "instrument": {
                                "name": "SPDR S&P 500 ETF",
                                "current_price": 450,
                                "allocation_asset_class": {"equity": 100},
                                "allocation_regions": {"north_america": 100},
                                "allocation_sectors": {"technology": 30, "healthcare": 15, "financials": 15, "consumer_discretionary": 20, "industrials": 20}
                            }
                        }
                    ]
                }
            ]
        }
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))
