"""
Agente Redactor de Informes - genera narrativas de análisis de portafolios.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from agents import function_tool, RunContextWrapper
from agents.extensions.models.litellm_model import LitellmModel

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
            logger.warning(f"Reporter: Posible prompt injection detectado: {pattern}")
            return "[INVALID INPUT DETECTED]"

    return text


@dataclass
class ReporterContext:
    """Contexto para el agente Reporter"""

    job_id: str
    portfolio_data: Dict[str, Any]
    user_data: Dict[str, Any]
    db: Optional[Any] = None  # Conexión a base de datos (opcional para pruebas)


def calculate_portfolio_metrics(portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calcular métricas básicas del portafolio."""
    metrics = {
        "total_value": 0,
        "cash_balance": 0,
        "num_accounts": len(portfolio_data.get("accounts", [])),
        "num_positions": 0,
        "unique_symbols": set(),
    }

    for account in portfolio_data.get("accounts", []):
        metrics["cash_balance"] += float(account.get("cash_balance", 0))
        positions = account.get("positions", [])
        metrics["num_positions"] += len(positions)

        for position in positions:
            symbol = position.get("symbol")
            if symbol:
                metrics["unique_symbols"].add(symbol)

            # Calcular valor si tenemos precio
            instrument = position.get("instrument", {})
            if instrument.get("current_price"):
                value = float(position.get("quantity", 0)) * float(instrument["current_price"])
                metrics["total_value"] += value

    metrics["total_value"] += metrics["cash_balance"]
    metrics["unique_symbols"] = len(metrics["unique_symbols"])

    return metrics


def format_portfolio_for_analysis(portfolio_data: Dict[str, Any], user_data: Dict[str, Any]) -> str:
    """Formatea los datos del portafolio para el análisis del agente."""
    metrics = calculate_portfolio_metrics(portfolio_data)

    lines = [
        f"Resumen del Portafolio:",
        f"- {metrics['num_accounts']} cuentas",
        f"- {metrics['num_positions']} posiciones totales",
        f"- {metrics['unique_symbols']} instrumentos únicos",
        f"- ${metrics['cash_balance']:,.2f} en efectivo",
        f"- ${metrics['total_value']:,.2f} valor total" if metrics["total_value"] > 0 else "",
        "",
        "Detalles de las cuentas:",
    ]

    for account in portfolio_data.get("accounts", []):
        name = account.get("name", "Desconocido")
        cash = float(account.get("cash_balance", 0))
        lines.append(f"\n{name} (${cash:,.2f} efectivo):")

        for position in account.get("positions", []):
            symbol = position.get("symbol")
            quantity = float(position.get("quantity", 0))
            instrument = position.get("instrument", {})
            name = instrument.get("name", "")

            # Incluir información de asignación si está disponible
            allocations = []
            if instrument.get("asset_class"):
                allocations.append(f"Clase de activo: {instrument['asset_class']}")
            if instrument.get("regions"):
                regions = ", ".join(
                    [f"{r['name']} {r['percentage']}%" for r in instrument["regions"][:2]]
                )
                allocations.append(f"Regiones: {regions}")

            alloc_str = f" ({', '.join(allocations)})" if allocations else ""
            lines.append(f"  - {symbol}: {quantity:,.2f} acciones{alloc_str}")

    # Añadir el contexto del usuario
    lines.extend(
        [
            "",
            "Perfil de Usuario:",
            f"- Años hasta la jubilación: {user_data.get('years_until_retirement', 'No especificado')}",
            f"- Objetivo de ingresos para la jubilación: ${user_data.get('target_retirement_income', 0):,.0f}/año",
        ]
    )

    return "\n".join(lines)


# herramienta update_report eliminada - el informe ahora se guarda directamente en lambda_handler


@function_tool
async def get_market_insights(
    wrapper: RunContextWrapper[ReporterContext], symbols: List[str]
) -> str:
    """
    Obtener insights de mercado desde la base de conocimiento S3 Vectors.

    Args:
        wrapper: Wrapper de contexto con job_id y base de datos
        symbols: Lista de símbolos para obtener insights

    Returns:
        Contexto e insights de mercado relevantes
    """
    try:
        import boto3

        # Obtener ID de la cuenta
        sts = boto3.client("sts")
        account_id = sts.get_caller_identity()["Account"]
        bucket = f"alex-vectors-{account_id}"

        # Obtener embeddings
        sagemaker_region = os.getenv("DEFAULT_AWS_REGION", "us-east-1")
        sagemaker = boto3.client("sagemaker-runtime", region_name=sagemaker_region)
        endpoint_name = os.getenv("SAGEMAKER_ENDPOINT", "alex-embedding-endpoint")
        query = f"market analysis {' '.join(symbols[:5])}" if symbols else "market outlook"

        response = sagemaker.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType="application/json",
            Body=json.dumps({"inputs": query}),
        )

        result = json.loads(response["Body"].read().decode())
        # Extraer embedding (manejar arreglos anidados)
        if isinstance(result, list) and result:
            embedding = result[0][0] if isinstance(result[0], list) else result[0]
        else:
            embedding = result

        # Buscar vectores
        s3v = boto3.client("s3vectors", region_name=sagemaker_region)
        response = s3v.query_vectors(
            vectorBucketName=bucket,
            indexName="financial-research",
            queryVector={"float32": embedding},
            topK=3,
            returnMetadata=True,
        )

        # Formatear los insights
        insights = []
        for vector in response.get("vectors", []):
            metadata = vector.get("metadata", {})
            text = metadata.get("text", "")[:200]
            if text:
                company = metadata.get("company_name", "")
                prefix = f"{company}: " if company else "- "
                insights.append(f"{prefix}{text}...")

        if insights:
            return "Insights de Mercado:\n" + "\n".join(insights)
        else:
            return "Insights de mercado no disponibles - continuando con el análisis estándar."

    except Exception as e:
        logger.warning(f"Reporter: No se pudieron obtener insights de mercado: {e}")
        return "Insights de mercado no disponibles - continuando con el análisis estándar."


def create_agent(job_id: str, portfolio_data: Dict[str, Any], user_data: Dict[str, Any], db=None):
    """Crear el agente reporter con herramientas y contexto."""

    # Obtener configuración del modelo
    model_id = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-3-7-sonnet-20250219-v1:0")
    # Establecer región para llamadas Bedrock de LiteLLM
    bedrock_region = os.getenv("BEDROCK_REGION", "us-west-2")
    logger.info(f"DEBUG: BEDROCK_REGION from env = {bedrock_region}")
    os.environ["AWS_REGION_NAME"] = bedrock_region
    logger.info(f"DEBUG: Se estableció AWS_REGION_NAME en {bedrock_region}")

    model = LitellmModel(model=f"bedrock/{model_id}")

    # Crear contexto
    context = ReporterContext(
        job_id=job_id, portfolio_data=portfolio_data, user_data=user_data, db=db
    )

    # Herramientas - solo get_market_insights ahora, el informe se guarda en lambda_handler
    tools = [get_market_insights]

    # Formatear portafolio para el análisis
    portfolio_summary = sanitize_user_input(
        format_portfolio_for_analysis(portfolio_data, user_data)
    )

    # Crear tarea
    task = f"""Analiza este portafolio de inversión y redacta un informe completo.

{portfolio_summary}

Tu tarea:
1. Primero, obtén insights de mercado para las principales posiciones usando get_market_insights()
2. Analiza el estado actual del portafolio, fortalezas y debilidades
3. Genera un informe de análisis detallado y profesional en formato markdown

El informe debe incluir:
- Resumen Ejecutivo
- Análisis de la Composición del Portafolio
- Evaluación de Riesgos
- Análisis de Diversificación
- Preparación para la Jubilación (basado en los objetivos del usuario)
- Recomendaciones
- Contexto de Mercado (a partir de los insights)

Proporciona tu análisis completo como resultado final en un formato markdown claro.
Haz que el informe sea informativo pero accesible para un inversor minorista."""

    return model, tools, task, context
