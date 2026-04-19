"""
Agente Chart Maker - crea datos de visualización para el análisis de portafolios.
"""

import os
import logging
from typing import Dict, Any

from agents.extensions.models.litellm_model import LitellmModel

from templates import CHARTER_INSTRUCTIONS, create_charter_task

logger = logging.getLogger()


def analyze_portfolio(portfolio_data: Dict[str, Any]) -> str:
    """
    Analiza el portafolio para entender su composición y calcular los principales indicadores.
    Devuelve un desglose detallado de posiciones, cuentas y asignaciones calculadas.
    """
    result = []
    total_value = 0.0
    position_values = {}
    account_totals = {}

    # Calcular los valores de posición y totales
    for account in portfolio_data.get("accounts", []):
        account_name = account.get("name", "Desconocido")
        account_type = account.get("type", "desconocido")
        # Manejar None o cash_balance ausente
        cash_balance = account.get("cash_balance")
        if cash_balance is None or cash_balance == "":
            cash = 0.0
        else:
            cash = float(cash_balance)

        if account_name not in account_totals:
            account_totals[account_name] = {"value": 0, "type": account_type, "positions": []}

        account_totals[account_name]["value"] += cash
        total_value += cash

        for position in account.get("positions", []):
            symbol = position.get("symbol")
            quantity = float(position.get("quantity", 0))
            instrument = position.get("instrument", {})
            # Manejar None o current_price ausente
            current_price = instrument.get("current_price")
            if current_price is None or current_price == "":
                price = 1.0  # Precio por defecto si no está disponible
                logger.warning(f"Charter: No hay precio para {symbol}, usando el valor por defecto de 1.0")
            else:
                price = float(current_price)
            value = quantity * price

            position_values[symbol] = position_values.get(symbol, 0) + value
            account_totals[account_name]["value"] += value
            account_totals[account_name]["positions"].append(
                {"symbol": symbol, "value": value, "instrument": instrument}
            )
            total_value += value

    # Construir resumen del análisis
    result.append("Análisis del Portafolio:")
    result.append(f"Valor Total: ${total_value:,.2f}")
    result.append(f"Número de Cuentas: {len(account_totals)}")
    result.append(f"Número de Posiciones: {len(position_values)}")

    result.append("\nDetalle por Cuenta:")
    for name, data in account_totals.items():
        pct = (data["value"] / total_value * 100) if total_value > 0 else 0
        result.append(f"  {name} ({data['type']}): ${data['value']:,.2f} ({pct:.1f}%)")

    result.append("\nPrincipales posiciones por valor:")
    sorted_positions = sorted(position_values.items(), key=lambda x: x[1], reverse=True)[:10]
    for symbol, value in sorted_positions:
        pct = (value / total_value * 100) if total_value > 0 else 0
        result.append(f"  {symbol}: ${value:,.2f} ({pct:.1f}%)")

    # Calcular asignaciones agregadas para el agente
    result.append("\nAsignaciones Calculadas:")
    
    # Agregación por clase de activo
    asset_classes = {}
    regions = {}
    sectors = {}
    
    for account in portfolio_data.get("accounts", []):
        for position in account.get("positions", []):
            symbol = position.get("symbol")
            quantity = float(position.get("quantity", 0))
            instrument = position.get("instrument", {})
            # Manejar None o current_price ausente
            current_price = instrument.get("current_price")
            if current_price is None or current_price == "":
                price = 1.0  # Precio por defecto si no está disponible
                logger.warning(f"Charter: No hay precio para {symbol}, usando el valor por defecto de 1.0")
            else:
                price = float(current_price)
            value = quantity * price
            
            # Agregar por clases de activo
            for asset_class, pct in instrument.get("allocation_asset_class", {}).items():
                asset_value = value * (pct / 100)
                asset_classes[asset_class] = asset_classes.get(asset_class, 0) + asset_value
            
            # Agregar por regiones
            for region, pct in instrument.get("allocation_regions", {}).items():
                region_value = value * (pct / 100)
                regions[region] = regions.get(region, 0) + region_value
            
            # Agregar por sectores
            for sector, pct in instrument.get("allocation_sectors", {}).items():
                sector_value = value * (pct / 100)
                sectors[sector] = sectors.get(sector, 0) + sector_value
    
    # Añadir efectivo a las clases de activo
    total_cash = sum(
        float(acc.get("cash_balance")) if acc.get("cash_balance") is not None else 0
        for acc in portfolio_data.get("accounts", [])
    )
    if total_cash > 0:
        asset_classes["cash"] = asset_classes.get("cash", 0) + total_cash
    
    result.append("\nClases de Activo:")
    for asset_class, value in sorted(asset_classes.items(), key=lambda x: x[1], reverse=True):
        result.append(f"  {asset_class}: ${value:,.2f}")
    
    result.append("\nRegiones Geográficas:")
    for region, value in sorted(regions.items(), key=lambda x: x[1], reverse=True):
        result.append(f"  {region}: ${value:,.2f}")
    
    result.append("\nSectores:")
    for sector, value in sorted(sectors.items(), key=lambda x: x[1], reverse=True)[:10]:
        result.append(f"  {sector}: ${value:,.2f}")

    return "\n".join(result)


def create_agent(job_id: str, portfolio_data: Dict[str, Any], db=None):
    """Crear el agente charter sin herramientas - devolverá JSON directamente."""
    
    # Obtener la configuración del modelo
    model_id = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-3-7-sonnet-20250219-v1:0")
    # Establecer la región para llamadas LiteLLM Bedrock
    bedrock_region = os.getenv("BEDROCK_REGION", "us-west-2")
    os.environ["AWS_REGION_NAME"] = bedrock_region
    
    logger.info(f"Charter: Creando agente con model_id={model_id}, región={bedrock_region}")
    logger.info(f"Charter: ID de trabajo: {job_id}")
    
    model = LitellmModel(model=f"bedrock/{model_id}")
    
    # Analizar el portafolio por adelantado
    portfolio_analysis = analyze_portfolio(portfolio_data)
    logger.info(f"Charter: Análisis de portafolio generado, longitud: {len(portfolio_analysis)}")
    
    # Crear la tarea usando la plantilla
    task = create_charter_task(portfolio_analysis, portfolio_data)
    
    logger.info(f"Charter: Tarea creada, longitud: {len(task)} caracteres")
    
    # Devolver modelo y tarea (sin herramientas ni contexto necesario)
    return model, task