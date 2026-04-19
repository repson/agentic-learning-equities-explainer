"""
Agente Orquestador de Planificación Financiera: coordina el análisis de la cartera a través de agentes especializados.
"""

import os
import json
import boto3
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass

from agents import function_tool, RunContextWrapper
from agents.extensions.models.litellm_model import LitellmModel

logger = logging.getLogger()

# Inicializar cliente de Lambda
lambda_client = boto3.client("lambda")

# Nombres de las funciones Lambda desde el entorno
TAGGER_FUNCTION = os.getenv("TAGGER_FUNCTION", "alex-tagger")
REPORTER_FUNCTION = os.getenv("REPORTER_FUNCTION", "alex-reporter")
CHARTER_FUNCTION = os.getenv("CHARTER_FUNCTION", "alex-charter")
RETIREMENT_FUNCTION = os.getenv("RETIREMENT_FUNCTION", "alex-retirement")
MOCK_LAMBDAS = os.getenv("MOCK_LAMBDAS", "false").lower() == "true"


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

        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(payload),
        )

        result = json.loads(response["Payload"].read())

        # Desempaquetar respuesta Lambda si tiene el formato estándar
        if isinstance(result, dict) and "statusCode" in result and "body" in result:
            if isinstance(result["body"], str):
                try:
                    result = json.loads(result["body"])
                except json.JSONDecodeError:
                    result = {"message": result["body"]}
            else:
                result = result["body"]

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
            response = lambda_client.invoke(
                FunctionName=TAGGER_FUNCTION,
                InvocationType="RequestResponse",
                Payload=json.dumps({"instruments": missing}),
            )

            result = json.loads(response["Payload"].read())

            if isinstance(result, dict) and "statusCode" in result:
                if result["statusCode"] == 200:
                    logger.info(
                        f"Planner: InstrumentTagger completado - Etiquetados {len(missing)} instrumentos"
                    )
                else:
                    logger.error(
                        f"Planner: InstrumentTagger falló con el status {result['statusCode']}"
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

    return model, tools, task, context
