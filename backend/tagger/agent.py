"""
Agente InstrumentTagger - Clasifica instrumentos financieros utilizando OpenAI Agents SDK.
"""

import os
from typing import List
import logging
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator, ConfigDict
from agents import Agent, Runner, trace
from agents.extensions.models.litellm_model import LitellmModel
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from litellm.exceptions import RateLimitError

from src.schemas import InstrumentCreate
from templates import TAGGER_INSTRUCTIONS, CLASSIFICATION_PROMPT

# Cargar variables de entorno (dotenv busca automáticamente hacia arriba en el árbol de directorios)
load_dotenv(override=True)

# Configurar logging
logger = logging.getLogger(__name__)

# Obtener configuración
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-3-7-sonnet-20250219-v1:0")
BEDROCK_REGION = os.getenv("BEDROCK_REGION", "us-west-2")


class AllocationBreakdown(BaseModel):
    """Porcentajes de asignación que deben sumar 100"""

    model_config = ConfigDict(extra="forbid")

    # Usaremos un enfoque simplificado con campos específicos
    # Clases de activos
    equity: float = Field(default=0.0, ge=0, le=100, description="Porcentaje de acciones (equity)")
    fixed_income: float = Field(default=0.0, ge=0, le=100, description="Porcentaje de renta fija")
    real_estate: float = Field(default=0.0, ge=0, le=100, description="Porcentaje inmobiliario")
    commodities: float = Field(default=0.0, ge=0, le=100, description="Porcentaje de materias primas")
    cash: float = Field(default=0.0, ge=0, le=100, description="Porcentaje de efectivo")
    alternatives: float = Field(default=0.0, ge=0, le=100, description="Porcentaje de alternativos")


class RegionAllocation(BaseModel):
    """Porcentajes de asignación regional"""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    north_america: float = Field(default=0.0, ge=0, le=100)
    europe: float = Field(default=0.0, ge=0, le=100)
    asia: float = Field(default=0.0, ge=0, le=100)
    latin_america: float = Field(default=0.0, ge=0, le=100)
    africa: float = Field(default=0.0, ge=0, le=100)
    middle_east: float = Field(default=0.0, ge=0, le=100)
    oceania: float = Field(default=0.0, ge=0, le=100)
    global_: float = Field(
        default=0.0, ge=0, le=100, alias="global", description="Global o diversificado"
    )
    international: float = Field(
        default=0.0, ge=0, le=100, description="Mercados desarrollados internacionales"
    )


class SectorAllocation(BaseModel):
    """Porcentajes de asignación sectorial"""

    model_config = ConfigDict(extra="forbid")

    technology: float = Field(default=0.0, ge=0, le=100)
    healthcare: float = Field(default=0.0, ge=0, le=100)
    financials: float = Field(default=0.0, ge=0, le=100)
    consumer_discretionary: float = Field(default=0.0, ge=0, le=100)
    consumer_staples: float = Field(default=0.0, ge=0, le=100)
    industrials: float = Field(default=0.0, ge=0, le=100)
    materials: float = Field(default=0.0, ge=0, le=100)
    energy: float = Field(default=0.0, ge=0, le=100)
    utilities: float = Field(default=0.0, ge=0, le=100)
    real_estate: float = Field(default=0.0, ge=0, le=100, description="Sector inmobiliario")
    communication: float = Field(default=0.0, ge=0, le=100)
    treasury: float = Field(default=0.0, ge=0, le=100, description="Bonos del tesoro")
    corporate: float = Field(default=0.0, ge=0, le=100, description="Bonos corporativos")
    mortgage: float = Field(default=0.0, ge=0, le=100, description="Valores respaldados por hipotecas")
    government_related: float = Field(
        default=0.0, ge=0, le=100, description="Bonos relacionados con gobiernos"
    )
    commodities: float = Field(default=0.0, ge=0, le=100, description="Materias primas")
    diversified: float = Field(default=0.0, ge=0, le=100, description="Sectores diversificados")
    other: float = Field(default=0.0, ge=0, le=100, description="Otros sectores")


class InstrumentClassification(BaseModel):
    """Salida estructurada para la clasificación de instrumentos"""

    model_config = ConfigDict(extra="forbid")

    symbol: str = Field(description="Símbolo (ticker) del instrumento")
    name: str = Field(description="Nombre del instrumento")
    instrument_type: str = Field(description="Tipo: etf, acción, fondo_mutuo, fondo_bonos, etc.")
    current_price: float = Field(description="Precio actual por acción en USD", gt=0)

    # Objetos de asignación separados
    allocation_asset_class: AllocationBreakdown = Field(description="Desglose por clase de activo")
    allocation_regions: RegionAllocation = Field(description="Desglose regional")
    allocation_sectors: SectorAllocation = Field(description="Desglose sectorial")

    @field_validator("allocation_asset_class")
    def validate_asset_class_sum(cls, v: AllocationBreakdown):
        total = v.equity + v.fixed_income + v.real_estate + v.commodities + v.cash + v.alternatives
        if abs(total - 100.0) > 3:  # Permitir pequeños errores de punto flotante
            raise ValueError(f"Las asignaciones de clase de activo deben sumar 100.0, se obtuvo {total}")
        return v

    @field_validator("allocation_regions")
    def validate_regions_sum(cls, v: RegionAllocation):
        total = (
            v.north_america
            + v.europe
            + v.asia
            + v.latin_america
            + v.africa
            + v.middle_east
            + v.oceania
            + v.global_
            + v.international
        )
        if abs(total - 100.0) > 3:
            raise ValueError(f"Las asignaciones regionales deben sumar 100.0, se obtuvo {total}")
        return v

    @field_validator("allocation_sectors")
    def validate_sectors_sum(cls, v: SectorAllocation):
        total = (
            v.technology
            + v.healthcare
            + v.financials
            + v.consumer_discretionary
            + v.consumer_staples
            + v.industrials
            + v.materials
            + v.energy
            + v.utilities
            + v.real_estate
            + v.communication
            + v.treasury
            + v.corporate
            + v.mortgage
            + v.government_related
            + v.commodities
            + v.diversified
            + v.other
        )
        if abs(total - 100.0) > 3:
            raise ValueError(f"Las asignaciones sectoriales deben sumar 100.0, se obtuvo {total}")
        return v


async def classify_instrument(
    symbol: str, name: str, instrument_type: str = "etf"
) -> InstrumentClassification:
    """
    Clasifica un instrumento financiero usando el SDK de OpenAI Agents.

    Args:
        symbol: Símbolo (ticker)
        name: Nombre del instrumento
        instrument_type: Tipo de instrumento

    Returns:
        Clasificación completa con asignaciones
    """
    try:
        # Inicializar el modelo
        model_id = BEDROCK_MODEL_ID

        # Establecer región para llamadas Bedrock de LiteLLM
        bedrock_region = os.getenv("BEDROCK_REGION", "us-west-2")
        os.environ["AWS_REGION_NAME"] = bedrock_region

        model = LitellmModel(model=f"bedrock/{model_id}")

        # Crear la tarea de clasificación
        task = CLASSIFICATION_PROMPT.format(
            symbol=symbol, name=name, instrument_type=instrument_type
        )

        # Ejecutar el agente (siguiendo el patrón de gameplan exactamente)
        with trace(f"Clasificar {symbol}"):
            agent = Agent(
                name="InstrumentTagger",
                instructions=TAGGER_INSTRUCTIONS,
                model=model,
                tools=[],  # No se necesitan herramientas para la clasificación
                output_type=InstrumentClassification,  # Especificar el tipo estructurado de salida
            )

            result = await Runner.run(agent, input=task, max_turns=5)

            # Extraer la salida estructurada de RunResult usando final_output_as
            return result.final_output_as(InstrumentClassification)

    except Exception as e:
        logger.error(f"Error al clasificar {symbol}: {e}")
        raise


async def tag_instruments(instruments: List[dict]) -> List[InstrumentClassification]:
    """
    Etiqueta múltiples instrumentos con lógica simple de reintento.

    Args:
        instruments: Lista de diccionarios con símbolo, nombre y opcionalmente instrument_type

    Returns:
        Lista de clasificaciones
    """
    import asyncio

    # Añadir decorador de reintento para las llamadas a classify_instrument
    @retry(
        retry=retry_if_exception_type(RateLimitError),
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        before_sleep=lambda retry_state: logger.info(
            f"Tagger: Limite de tasa alcanzado, reintentando en {retry_state.next_action.sleep} segundos..."
        ),
    )
    async def classify_with_retry(symbol, name, instrument_type):
        return await classify_instrument(symbol, name, instrument_type)

    # Procesar instrumentos secuencialmente con pequeño retraso
    results = []
    for i, instrument in enumerate(instruments):
        # Pequeño retraso entre solicitudes para evitar límites de tasa
        if i > 0:
            await asyncio.sleep(0.5)

        try:
            classification = await classify_with_retry(
                symbol=instrument["symbol"],
                name=instrument.get("name", ""),
                instrument_type=instrument.get("instrument_type", "etf"),
            )
            logger.info(f"Clasificado con éxito {instrument['symbol']}")
            results.append(classification)
        except Exception as e:
            logger.error(f"No se pudo clasificar {instrument['symbol']}: {e}")
            results.append(None)

    # Filtrar valores None
    return [r for r in results if r is not None]


def classification_to_db_format(classification: InstrumentClassification) -> InstrumentCreate:
    """
    Convierte la clasificación al formato de base de datos.

    Args:
        classification: La clasificación generada por la IA

    Returns:
        Datos del instrumento listos para la base de datos
    """
    # Convertir objetos de asignación a diccionarios
    asset_class_dict = {
        "equity": classification.allocation_asset_class.equity,
        "fixed_income": classification.allocation_asset_class.fixed_income,
        "real_estate": classification.allocation_asset_class.real_estate,
        "commodities": classification.allocation_asset_class.commodities,
        "cash": classification.allocation_asset_class.cash,
        "alternatives": classification.allocation_asset_class.alternatives,
    }
    # Eliminar valores cero
    asset_class_dict = {k: v for k, v in asset_class_dict.items() if v > 0}

    regions_dict = {
        "north_america": classification.allocation_regions.north_america,
        "europe": classification.allocation_regions.europe,
        "asia": classification.allocation_regions.asia,
        "latin_america": classification.allocation_regions.latin_america,
        "africa": classification.allocation_regions.africa,
        "middle_east": classification.allocation_regions.middle_east,
        "oceania": classification.allocation_regions.oceania,
        "global": classification.allocation_regions.global_,
        "international": classification.allocation_regions.international,
    }
    # Eliminar valores cero
    regions_dict = {k: v for k, v in regions_dict.items() if v > 0}

    sectors_dict = {
        "technology": classification.allocation_sectors.technology,
        "healthcare": classification.allocation_sectors.healthcare,
        "financials": classification.allocation_sectors.financials,
        "consumer_discretionary": classification.allocation_sectors.consumer_discretionary,
        "consumer_staples": classification.allocation_sectors.consumer_staples,
        "industrials": classification.allocation_sectors.industrials,
        "materials": classification.allocation_sectors.materials,
        "energy": classification.allocation_sectors.energy,
        "utilities": classification.allocation_sectors.utilities,
        "real_estate": classification.allocation_sectors.real_estate,
        "communication": classification.allocation_sectors.communication,
        "treasury": classification.allocation_sectors.treasury,
        "corporate": classification.allocation_sectors.corporate,
        "mortgage": classification.allocation_sectors.mortgage,
        "government_related": classification.allocation_sectors.government_related,
        "commodities": classification.allocation_sectors.commodities,
        "diversified": classification.allocation_sectors.diversified,
        "other": classification.allocation_sectors.other,
    }
    # Eliminar valores cero
    sectors_dict = {k: v for k, v in sectors_dict.items() if v > 0}

    return InstrumentCreate(
        symbol=classification.symbol,
        name=classification.name,
        instrument_type=classification.instrument_type,
        current_price=Decimal(
            str(classification.current_price)
        ),  # Usar precio real de la clasificación
        allocation_asset_class=asset_class_dict,
        allocation_regions=regions_dict,
        allocation_sectors=sectors_dict,
    )
