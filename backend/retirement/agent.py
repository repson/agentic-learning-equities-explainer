"""
Agente Especialista en Jubilación - proporciona análisis y proyecciones de planificación de retiro.
"""

import os
import json
import logging
import random
from typing import Dict, Any
from datetime import datetime

# No se necesitan herramientas - agente simplificado
from agents.extensions.models.litellm_model import LitellmModel

logger = logging.getLogger()

# Contexto eliminado - ya no es necesario sin herramientas


def calculate_portfolio_value(portfolio_data: Dict[str, Any]) -> float:
    """Calcular el valor actual de la cartera."""
    total_value = 0.0

    for account in portfolio_data.get("accounts", []):
        cash = float(account.get("cash_balance", 0))
        total_value += cash

        for position in account.get("positions", []):
            quantity = float(position.get("quantity", 0))
            instrument = position.get("instrument", {})
            price = float(instrument.get("current_price", 100))
            total_value += quantity * price

    return total_value


def calculate_asset_allocation(portfolio_data: Dict[str, Any]) -> Dict[str, float]:
    """Calcular los porcentajes de asignación de activos."""
    total_equity = 0.0
    total_bonds = 0.0
    total_real_estate = 0.0
    total_commodities = 0.0
    total_cash = 0.0
    total_value = 0.0

    for account in portfolio_data.get("accounts", []):
        cash = float(account.get("cash_balance", 0))
        total_cash += cash
        total_value += cash

        for position in account.get("positions", []):
            quantity = float(position.get("quantity", 0))
            instrument = position.get("instrument", {})
            price = float(instrument.get("current_price", 100))
            value = quantity * price
            total_value += value

            # Obtener asignación de la clase de activo
            asset_allocation = instrument.get("allocation_asset_class", {})
            if asset_allocation:
                total_equity += value * asset_allocation.get("equity", 0) / 100
                total_bonds += value * asset_allocation.get("fixed_income", 0) / 100
                total_real_estate += value * asset_allocation.get("real_estate", 0) / 100
                total_commodities += value * asset_allocation.get("commodities", 0) / 100

    if total_value == 0:
        return {"equity": 0, "bonds": 0, "real_estate": 0, "commodities": 0, "cash": 0}

    return {
        "equity": total_equity / total_value,
        "bonds": total_bonds / total_value,
        "real_estate": total_real_estate / total_value,
        "commodities": total_commodities / total_value,
        "cash": total_cash / total_value,
    }


def run_monte_carlo_simulation(
    current_value: float,
    years_until_retirement: int,
    target_annual_income: float,
    asset_allocation: Dict[str, float],
    num_simulations: int = 500,
) -> Dict[str, Any]:
    """Ejecutar simulación de Monte Carlo para la planificación de retiro."""

    # Parámetros de retorno históricos (anualizados)
    equity_return_mean = 0.07
    equity_return_std = 0.18
    bond_return_mean = 0.04
    bond_return_std = 0.05
    real_estate_return_mean = 0.06
    real_estate_return_std = 0.12

    successful_scenarios = 0
    final_values = []
    years_lasted = []

    for _ in range(num_simulations):
        portfolio_value = current_value

        # Fase de acumulación
        for _ in range(years_until_retirement):
            equity_return = random.gauss(equity_return_mean, equity_return_std)
            bond_return = random.gauss(bond_return_mean, bond_return_std)
            real_estate_return = random.gauss(real_estate_return_mean, real_estate_return_std)

            portfolio_return = (
                asset_allocation["equity"] * equity_return
                + asset_allocation["bonds"] * bond_return
                + asset_allocation["real_estate"] * real_estate_return
                + asset_allocation["cash"] * 0.02
            )

            portfolio_value = portfolio_value * (1 + portfolio_return)
            portfolio_value += 10000  # Aportación anual

        # Fase de retiro
        retirement_years = 30
        annual_withdrawal = target_annual_income
        years_income_lasted = 0

        for year in range(retirement_years):
            if portfolio_value <= 0:
                break

            # Ajuste por inflación (3% por año)
            annual_withdrawal *= 1.03

            equity_return = random.gauss(equity_return_mean, equity_return_std)
            bond_return = random.gauss(bond_return_mean, bond_return_std)
            real_estate_return = random.gauss(real_estate_return_mean, real_estate_return_std)

            portfolio_return = (
                asset_allocation["equity"] * equity_return
                + asset_allocation["bonds"] * bond_return
                + asset_allocation["real_estate"] * real_estate_return
                + asset_allocation["cash"] * 0.02
            )

            portfolio_value = portfolio_value * (1 + portfolio_return) - annual_withdrawal

            if portfolio_value > 0:
                years_income_lasted += 1

        final_values.append(max(0, portfolio_value))
        years_lasted.append(years_income_lasted)

        if years_income_lasted >= retirement_years:
            successful_scenarios += 1

    # Calcular estadísticas
    final_values.sort()
    success_rate = (successful_scenarios / num_simulations) * 100

    # Calcular valor esperado en la jubilación
    expected_return = (
        asset_allocation["equity"] * equity_return_mean
        + asset_allocation["bonds"] * bond_return_mean
        + asset_allocation["real_estate"] * real_estate_return_mean
        + asset_allocation["cash"] * 0.02
    )
    expected_value_at_retirement = current_value
    for _ in range(years_until_retirement):
        expected_value_at_retirement *= 1 + expected_return
        expected_value_at_retirement += 10000

    return {
        "success_rate": round(success_rate, 1),
        "median_final_value": round(final_values[num_simulations // 2], 2),
        "percentile_10": round(final_values[num_simulations // 10], 2),
        "percentile_90": round(final_values[9 * num_simulations // 10], 2),
        "average_years_lasted": round(sum(years_lasted) / len(years_lasted), 1),
        "expected_value_at_retirement": round(expected_value_at_retirement, 2),
    }


def generate_projections(
    current_value: float,
    years_until_retirement: int,
    asset_allocation: Dict[str, float],
    current_age: int,
) -> list:
    """Generar proyecciones de jubilación simplificadas."""

    # Rendimientos esperados
    expected_return = (
        asset_allocation["equity"] * 0.07
        + asset_allocation["bonds"] * 0.04
        + asset_allocation["real_estate"] * 0.06
        + asset_allocation["cash"] * 0.02
    )

    projections = []
    portfolio_value = current_value

    # Mostrar solo hitos clave (cada 5 años)
    milestone_years = list(range(0, years_until_retirement + 31, 5))

    for year in milestone_years:
        age = current_age + year

        if year <= years_until_retirement:
            # Calcular acumulación
            for _ in range(min(5, year)):
                portfolio_value *= 1 + expected_return
                portfolio_value += 10000
            phase = "accumulation"
            annual_income = 0
        else:
            # Calcular retiros en jubilación
            withdrawal_rate = 0.04
            annual_income = portfolio_value * withdrawal_rate
            years_in_retirement = min(5, year - years_until_retirement)
            for _ in range(years_in_retirement):
                portfolio_value = portfolio_value * (1 + expected_return) - annual_income
            phase = "retirement"

        if portfolio_value > 0:
            projections.append(
                {
                    "year": year,
                    "age": age,
                    "portfolio_value": round(portfolio_value, 2),
                    "annual_income": round(annual_income, 2),
                    "phase": phase,
                }
            )

    return projections


# Herramienta eliminada - el análisis ahora se guarda directamente en lambda_handler


def create_agent(
    job_id: str, portfolio_data: Dict[str, Any], user_preferences: Dict[str, Any], db=None
):
    """Crear el agente de retiro con herramientas y contexto."""

    # Obtener configuración del modelo
    model_id = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-3-7-sonnet-20250219-v1:0")
    # Configurar región para llamadas LiteLLM Bedrock
    bedrock_region = os.getenv("BEDROCK_REGION", "us-west-2")
    os.environ["AWS_REGION_NAME"] = bedrock_region

    model = LitellmModel(model=f"bedrock/{model_id}")

    # Extraer preferencias del usuario
    years_until_retirement = user_preferences.get("years_until_retirement", 30)
    target_income = user_preferences.get("target_retirement_income", 80000)
    current_age = user_preferences.get("current_age", 40)

    # Calcular métricas de la cartera
    portfolio_value = calculate_portfolio_value(portfolio_data)
    allocation = calculate_asset_allocation(portfolio_data)

    # Ejecutar simulación de Monte Carlo
    monte_carlo = run_monte_carlo_simulation(
        portfolio_value, years_until_retirement, target_income, allocation, num_simulations=500
    )

    # Generar proyecciones
    projections = generate_projections(
        portfolio_value, years_until_retirement, allocation, current_age
    )

    # Ya no se necesita contexto - agente simplificado

    # No se necesitan herramientas - el agente devolverá el análisis como salida final
    tools = []

    # Formatear contexto integral para el agente
    task = f"""
# Contexto de Análisis de Cartera

## Situación Actual
- Valor de la Cartera: ${portfolio_value:,.0f}
- Asignación de Activos: {", ".join([f"{k.title()}: {v:.0%}" for k, v in allocation.items() if v > 0])}
- Años para la Jubilación: {years_until_retirement}
- Ingreso Anual Objetivo: ${target_income:,.0f}
- Edad Actual: {current_age}

## Resultados de la Simulación de Monte Carlo (500 escenarios)
- Tasa de Éxito: {monte_carlo["success_rate"]}% (probabilidad de sostener el ingreso de retiro por 30 años)
- Valor Esperado de la Cartera al Jubilarse: ${monte_carlo["expected_value_at_retirement"]:,.0f}
- Resultado del Percentil 10: ${monte_carlo["percentile_10"]:,.0f} (peor caso)
- Valor Final Mediano: ${monte_carlo["median_final_value"]:,.0f}
- Resultado del Percentil 90: ${monte_carlo["percentile_90"]:,.0f} (mejor caso)
- Promedio de Años que Dura la Cartera: {monte_carlo["average_years_lasted"]} años

## Proyecciones Clave (Hitos)
"""

    for proj in projections[:6]:
        if proj["phase"] == "accumulation":
            task += f"- Edad {proj['age']}: ${proj['portfolio_value']:,.0f} (acumulando patrimonio)\n"
        else:
            task += f"- Edad {proj['age']}: ${proj['portfolio_value']:,.0f} (ingreso anual: ${proj['annual_income']:,.0f})\n"

    task += f"""

## Factores de Riesgo a Considerar
- Riesgo de secuencia de retornos (malos retornos al inicio de la jubilación)
- Impacto de la inflación (se asume 3%)
- Costos de salud en la jubilación
- Riesgo de longevidad (vivir más de 30 años)
- Volatilidad del mercado (desviación estándar de renta variable: 18%)

## Análisis de Tasa de Retiro Segura
- Regla del 4%: ${portfolio_value * 0.04:,.0f} ingreso anual inicial
- Ingreso Objetivo: ${target_income:,.0f}
- Diferencia: ${target_income - (portfolio_value * 0.04):,.0f}

Tu tarea: Analiza estos datos de preparación para el retiro y proporciona un análisis de jubilación integral que incluya:
1. Evaluación clara de la preparación para el retiro
2. Recomendaciones específicas para mejorar la tasa de éxito
3. Estrategias para mitigar riesgos
4. Acciones sugeridas con cronograma

Proporciona tu análisis en formato markdown claro con números específicos y recomendaciones accionables.
"""

    return model, tools, task
