"""
Manejador Lambda del Agente Generador de Reportes
"""

import os
import json
import asyncio
import logging
from typing import Dict, Any
from datetime import datetime

from agents import Agent, Runner, trace
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from litellm.exceptions import RateLimitError
from judge import evaluate

GUARD_AGAINST_SCORE = 0.3  # Proteger contra puntajes demasiado bajos

try:
    from dotenv import load_dotenv

    load_dotenv(override=True)
except ImportError:
    pass

# Importar el paquete de base de datos
from src import Database

from templates import REPORTER_INSTRUCTIONS
from agent import create_agent, ReporterContext
from observability import observe

logger = logging.getLogger()
logger.setLevel(logging.INFO)


@retry(
    retry=retry_if_exception_type(RateLimitError),
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    before_sleep=lambda retry_state: logger.info(
        f"Reporter: Límite de tasa alcanzado, reintentando en {retry_state.next_action.sleep} segundos..."
    ),
)
async def run_reporter_agent(
    job_id: str,
    portfolio_data: Dict[str, Any],
    user_data: Dict[str, Any],
    db=None,
    observability=None,
) -> Dict[str, Any]:
    """Ejecuta el agente generador de reportes para generar el análisis."""

    # Crear agente con herramientas y contexto
    model, tools, task, context = create_agent(job_id, portfolio_data, user_data, db)

    # Ejecutar el agente con contexto
    with trace("Reporter Agent"):
        agent = Agent[ReporterContext](  # Especificar el tipo de contexto
            name="Report Writer", instructions=REPORTER_INSTRUCTIONS, model=model, tools=tools
        )

        result = await Runner.run(
            agent,
            input=task,
            context=context,  # Pasar el contexto
            max_turns=10,
        )

        response = result.final_output

        if observability:
            with observability.start_as_current_span(name="judge") as span:
                evaluation = await evaluate(REPORTER_INSTRUCTIONS, task, response)
                score = evaluation.score / 100
                comment = evaluation.feedback
                span.score(name="Judge", value=score, data_type="NUMERIC", comment=comment)
                observation = f"Puntuación: {score} - Comentario: {comment}"
                observability.create_event(name="Evento del Juez", status_message=observation)
                if score < GUARD_AGAINST_SCORE:
                    logger.error(f"La puntuación del Reportero es demasiado baja: {score}")
                    response = "Lo siento, no puedo generar un informe para usted. Por favor, inténtelo de nuevo más tarde."

        # Guardar el informe en la base de datos
        report_payload = {
            "content": response,
            "generated_at": datetime.utcnow().isoformat(),
            "agent": "reporter",
        }

        success = db.jobs.update_report(job_id, report_payload)

        if not success:
            logger.error(f"No se pudo guardar el informe para el trabajo {job_id}")

        return {
            "success": success,
            "message": "Informe generado y almacenado"
            if success
            else "Informe generado pero no se pudo guardar",
            "final_output": result.final_output,
        }


def lambda_handler(event, context):
    """
    Manejador Lambda esperando job_id, portfolio_data y user_data en el evento.

    Evento esperado:
    {
        "job_id": "uuid",
        "portfolio_data": {...},
        "user_data": {...}
    }
    """
    # Encapsular todo el manejador en el contexto de observabilidad
    with observe() as observability:
        try:
            logger.info(f"Lambda del Reportero invocada con evento: {json.dumps(event)[:500]}")

            # Analizar evento
            if isinstance(event, str):
                event = json.loads(event)

            job_id = event.get("job_id")
            if not job_id:
                return {"statusCode": 400, "body": json.dumps({"error": "job_id es obligatorio"})}

            # Inicializar base de datos
            db = Database()

            portfolio_data = event.get("portfolio_data")
            if not portfolio_data:
                # Intentar cargar desde la base de datos
                try:
                    job = db.jobs.find_by_id(job_id)
                    if job:
                        user_id = job["clerk_user_id"]

                        if observability:
                            observability.create_event(
                                name="¡Reportero Iniciado!", status_message="OK"
                            )
                        user = db.users.find_by_clerk_id(user_id)
                        accounts = db.accounts.find_by_user(user_id)

                        portfolio_data = {"user_id": user_id, "job_id": job_id, "accounts": []}

                        for account in accounts:
                            positions = db.positions.find_by_account(account["id"])
                            account_data = {
                                "id": account["id"],
                                "name": account["account_name"],
                                "type": account.get("account_type", "investment"),
                                "cash_balance": float(account.get("cash_balance", 0)),
                                "positions": [],
                            }

                            for position in positions:
                                instrument = db.instruments.find_by_symbol(position["symbol"])
                                if instrument:
                                    account_data["positions"].append(
                                        {
                                            "symbol": position["symbol"],
                                            "quantity": float(position["quantity"]),
                                            "instrument": instrument,
                                        }
                                    )

                            portfolio_data["accounts"].append(account_data)
                    else:
                        return {
                            "statusCode": 404,
                            "body": json.dumps({"error": f"Trabajo {job_id} no encontrado"}),
                        }
                except Exception as e:
                    logger.error(f"No se pudo cargar el portafolio desde la base de datos: {e}")
                    return {
                        "statusCode": 400,
                        "body": json.dumps({"error": "No se proporcionaron datos de portafolio"}),
                    }

            user_data = event.get("user_data", {})
            if not user_data:
                # Intentar cargar desde la base de datos
                try:
                    job = db.jobs.find_by_id(job_id)
                    if job and job.get("clerk_user_id"):
                        status = f"ID de Trabajo: {job_id} ID de Usuario Clerk: {job['clerk_user_id']}"
                        if observability:
                            observability.create_event(
                                name="Reportero a punto de ejecutarse", status_message=status
                            )
                        user = db.users.find_by_clerk_id(job["clerk_user_id"])
                        if user:
                            user_data = {
                                "years_until_retirement": user.get("years_until_retirement", 30),
                                "target_retirement_income": float(
                                    user.get("target_retirement_income", 80000)
                                ),
                            }
                        else:
                            user_data = {
                                "years_until_retirement": 30,
                                "target_retirement_income": 80000,
                            }
                except Exception as e:
                    logger.warning(f"No se pudieron cargar datos de usuario: {e}. Usando valores predeterminados.")
                    user_data = {"years_until_retirement": 30, "target_retirement_income": 80000}

            # Ejecutar el agente
            result = asyncio.run(
                run_reporter_agent(job_id, portfolio_data, user_data, db, observability)
            )

            logger.info(f"Reportero completado para el trabajo {job_id}")

            return {"statusCode": 200, "body": json.dumps(result)}

        except Exception as e:
            logger.error(f"Error en el reportero: {e}", exc_info=True)
            return {"statusCode": 500, "body": json.dumps({"success": False, "error": str(e)})}


# Para pruebas locales
if __name__ == "__main__":
    test_event = {
        "job_id": "550e8400-e29b-41d4-a716-446655440002",
        "portfolio_data": {
            "accounts": [
                {
                    "name": "401(k)",
                    "cash_balance": 5000,
                    "positions": [
                        {
                            "symbol": "SPY",
                            "quantity": 100,
                            "instrument": {
                                "name": "SPDR S&P 500 ETF",
                                "current_price": 450,
                                "asset_class": "equity",
                            },
                        }
                    ],
                }
            ]
        },
        "user_data": {"years_until_retirement": 25, "target_retirement_income": 75000},
    }

    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))
