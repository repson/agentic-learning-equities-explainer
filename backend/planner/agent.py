"""
Agente Orquestador de Planificación Financiera: coordina el análisis de la cartera a través de agentes especializados.
"""

import os
import json
import boto3
import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass

from agents import function_tool, RunContextWrapper
from agents.extensions.models.litellm_model import LitellmModel
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger()


def sanitize_user_input(text: str) -> str:
    """Remover intentos potenciales de prompt injection."""
    dangerous_patterns = [
        "ignore previous instructions",
        "disregard all prior",
        "forget everything",
        "new instructions:",
        "system:",
        "assistant:",
    ]

    text_lower = text.lower()
    for pattern in dangerous_patterns:
        if pattern in text_lower:
            logger.warning(f"Planner: Posible prompt injection detectado: {pattern}")
            return "[INVALID INPUT DETECTED]"

    return text

# Inicializar cliente de Lambda
lambda_client = boto3.client("lambda")

# Nombres de las funciones Lambda desde el entorno
TAGGER_FUNCTION = os.getenv("TAGGER_FUNCTION", "alex-tagger")
REPORTER_FUNCTION = os.getenv("REPORTER_FUNCTION", "alex-reporter")
CHARTER_FUNCTION = os.getenv("CHARTER_FUNCTION", "alex-charter")
RETIREMENT_FUNCTION = os.getenv("RETIREMENT_FUNCTION", "alex-retirement")
MOCK_LAMBDAS = os.getenv("MOCK_LAMBDAS", "false").lower() == "true"


class AgentTemporaryError(Exception):
    """Error temporal de agente que debe reintentarse."""


def _is_retryable_lambda_error(result: Dict[str, Any]) -> bool:
    """Detectar respuestas de Lambda que ameritan reintento."""
    error_type = str(result.get("error_type", "")).upper()
    if error_type in {"RATE_LIMIT", "THROTTLED", "TIMEOUT"}:
        return True

    status_code = result.get("statusCode")
    if isinstance(status_code, int) and status_code >= 500:
        return True

    error_text = str(result.get("error", "")).lower()
    if any(token in error_text for token in ["throttl", "timeout", "rate limit", "too many requests"]):
        return True

    return False


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((AgentTemporaryError, TimeoutError)),
)
async def invoke_agent_with_retry(
    agent_name: str, payload: Dict[str, Any], function_name: Optional[str] = None
) -> Dict[str, Any]:
    """Invocar agente con reintentos automaticos para errores temporales."""
    lambda_name = function_name or f"alex-{agent_name.lower()}"

    try:
        response = await asyncio.to_thread(
            lambda_client.invoke,
            FunctionName=lambda_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(payload),
        )

        result = json.loads(response["Payload"].read())

        if isinstance(result, dict) and "statusCode" in result and "body" in result:
            if isinstance(result["body"], str):
                try:
                    result = json.loads(result["body"])
                except json.JSONDecodeError:
                    result = {"message": result["body"]}
            else:
                result = result["body"]

        if isinstance(result, dict) and _is_retryable_lambda_error(result):
            raise AgentTemporaryError(f"Error temporal detectado en {agent_name}: {result}")

        return result

    except Exception as e:
        logger.warning(f"Invocacion de agente {agent_name} fallida: {e}")
        error_msg = str(e).lower()
        if any(token in error_msg for token in ["throttl", "timeout", "rate limit", "too many requests"]):
            raise AgentTemporaryError(f"Error temporal en {agent_name}: {e}")
        raise


@dataclass
class PlannerContext:
    """Contexto para las herramientas del agente de planificación."""
    job_id: str


async def invoke_lambda_agent(
    agent_name: str, function_name: str, payload: Dict[str, Any]
) -> Dict[str, Any]:
    """Invocar una función Lambda para un agente."""

    # Para pruebas locales con agentes simulados
    if MOCK_LAMBDAS:
        logger.info(f"[MOCK] Se invocaría {agent_name} con el payload: {json.dumps(payload)[:200]}")
        return {"success": True, "message": f"[Mock] {agent_name} completado", "mock": True}

    try:
        logger.info(f"Invocando Lambda de {agent_name}: {function_name}")

        # Invocacion resiliente con reintentos para errores temporales
        result = await invoke_agent_with_retry(agent_name, payload, function_name=function_name)

        logger.info(f"{agent_name} completado con éxito")
        return result

    except Exception as e:
        logger.error(f"Error al invocar {agent_name}: {e}")
        return {"error": str(e)}


def handle_missing_instruments(job_id: str, db) -> None:
    """
    Verificar y etiquetar los instrumentos que faltan datos de asignación.
    Esto se hace automáticamente antes de que se ejecute el agente.
    """
    logger.info("Planner: Comprobando instrumentos sin datos de asignación...")

    # Obtener datos del trabajo y del portafolio
    job = db.jobs.find_by_id(job_id)
    if not job:
        logger.error(f"Trabajo {job_id} no encontrado")
        return

    user_id = job["clerk_user_id"]
    accounts = db.accounts.find_by_user(user_id)

    missing = []
    for account in accounts:
        positions = db.positions.find_by_account(account["id"])
        for position in positions:
            instrument = db.instruments.find_by_symbol(position["symbol"])
            if instrument:
                has_allocations = bool(
                    instrument.get("allocation_regions")
                    and instrument.get("allocation_sectors")
                    and instrument.get("allocation_asset_class")
                )
                if not has_allocations:
                    missing.append(
                        {"symbol": position["symbol"], "name": instrument.get("name", "")}
                    )
            else:
                missing.append({"symbol": position["symbol"], "name": ""})

    if missing:
        logger.info(
            f"Planner: Encontrados {len(missing)} instrumentos que necesitan clasificación: {[m['symbol'] for m in missing]}"
        )

        try:
            result = asyncio.run(
                invoke_agent_with_retry(
                    "Tagger",
                    {"instruments": missing},
                    function_name=TAGGER_FUNCTION,
                )
            )

            if isinstance(result, dict) and "statusCode" in result:
                if result["statusCode"] == 200:
                    logger.info(
                        f"Planner: InstrumentTagger completado - Etiquetados {len(missing)} instrumentos"
                    )
                else:
                    logger.error(
                        f"Planner: InstrumentTagger falló con el status {result['statusCode']}"
                    )
            else:
                logger.info(
                    f"Planner: InstrumentTagger completado - Etiquetados {len(missing)} instrumentos"
                )

        except Exception as e:
            logger.error(f"Planner: Error al etiquetar instrumentos: {e}")
    else:
        logger.info("Planner: Todos los instrumentos tienen datos de asignación")


def load_portfolio_summary(job_id: str, db) -> Dict[str, Any]:
    """Cargar solo estadísticas básicas del resumen de la cartera."""
    try:
        job = db.jobs.find_by_id(job_id)
        if not job:
            raise ValueError(f"Trabajo {job_id} no encontrado")

        user_id = job["clerk_user_id"]
        user = db.users.find_by_clerk_id(user_id)
        if not user:
            raise ValueError(f"Usuario {user_id} no encontrado")

        accounts = db.accounts.find_by_user(user_id)
        
        # Calcular estadísticas simples del resumen
        total_value = 0.0
        total_positions = 0
        total_cash = 0.0
        
        for account in accounts:
            total_cash += float(account.get("cash_balance", 0))
            positions = db.positions.find_by_account(account["id"])
            total_positions += len(positions)
            
            # Sumar valores de las posiciones
            for position in positions:
                instrument = db.instruments.find_by_symbol(position["symbol"])
                if instrument and instrument.get("current_price"):
                    price = float(instrument["current_price"])
                    quantity = float(position["quantity"])
                    total_value += price * quantity
        
        total_value += total_cash
        
        # Devolver solo estadísticas del resumen
        return {
            "total_value": total_value,
            "num_accounts": len(accounts),
            "num_positions": total_positions,
            "years_until_retirement": user.get("years_until_retirement", 30),
            "target_retirement_income": float(user.get("target_retirement_income", 80000))
        }

    except Exception as e:
        logger.error(f"Error al cargar el resumen de la cartera: {e}")
        raise


async def invoke_reporter_internal(job_id: str) -> str:
    """
    Invoca el Lambda del Generador de Reportes para generar la narrativa del análisis de la cartera.

    Args:
        job_id: El ID del trabajo para el análisis

    Returns:
        Mensaje de confirmación
    """
    result = await invoke_lambda_agent("Reporter", REPORTER_FUNCTION, {"job_id": job_id})

    if "error" in result:
        return f"El agente Reporter falló: {result['error']}"

    return "El agente Reporter se completó correctamente. La narrativa del análisis de la cartera ha sido generada y guardada."


async def invoke_charter_internal(job_id: str) -> str:
    """
    Invoca el Lambda del Generador de Gráficas para crear las visualizaciones de la cartera.

    Args:
        job_id: El ID del trabajo para el análisis

    Returns:
        Mensaje de confirmación
    """
    result = await invoke_lambda_agent(
        "Charter", CHARTER_FUNCTION, {"job_id": job_id}
    )

    if "error" in result:
        return f"El agente Charter falló: {result['error']}"

    return "El agente Charter se completó correctamente. Las visualizaciones del portafolio han sido creadas y guardadas."


async def invoke_retirement_internal(job_id: str) -> str:
    """
    Invoca el Lambda del Especialista de Retiro para proyecciones de jubilación.

    Args:
        job_id: El ID del trabajo para el análisis

    Returns:
        Mensaje de confirmación
    """
    result = await invoke_lambda_agent("Retirement", RETIREMENT_FUNCTION, {"job_id": job_id})

    if "error" in result:
        return f"El agente Retirement falló: {result['error']}"

    return "El agente Retirement se completó correctamente. Las proyecciones de jubilación han sido calculadas y guardadas."



@function_tool
async def invoke_reporter(wrapper: RunContextWrapper[PlannerContext]) -> str:
    """Invoca el agente Generador de Reportes para generar la narrativa del análisis de la cartera."""
    return await invoke_reporter_internal(wrapper.context.job_id)

@function_tool
async def invoke_charter(wrapper: RunContextWrapper[PlannerContext]) -> str:
    """Invoca el agente Generador de Gráficas para crear visualizaciones de la cartera."""
    return await invoke_charter_internal(wrapper.context.job_id)

@function_tool
async def invoke_retirement(wrapper: RunContextWrapper[PlannerContext]) -> str:
    """Invoca el agente Especialista de Retiro para proyecciones de jubilación."""
    return await invoke_retirement_internal(wrapper.context.job_id)


def create_agent(job_id: str, portfolio_summary: Dict[str, Any], db):
    """Crear el agente orquestador con herramientas."""
    
    # Crear contexto para las herramientas
    context = PlannerContext(job_id=job_id)

    # Obtener configuración del modelo
    model_id = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-3-7-sonnet-20250219-v1:0")
    # Establecer región para llamadas a LiteLLM Bedrock
    bedrock_region = os.getenv("BEDROCK_REGION", "us-west-2")
    os.environ["AWS_REGION_NAME"] = bedrock_region

    model = LitellmModel(model=f"bedrock/{model_id}")

    tools = [
        invoke_reporter,
        invoke_charter,
        invoke_retirement,
    ]

    # Crear contexto mínimo de tarea
    task = f"""Trabajo {job_id} tiene {portfolio_summary['num_positions']} posiciones.
Retiro: {portfolio_summary['years_until_retirement']} años.

Llama a los agentes apropiados."""

    task = sanitize_user_input(task)

    return model, tools, task, context
