from agents import Agent, Runner
from pydantic import BaseModel, Field
import os
import logging
from agents.extensions.models.litellm_model import LitellmModel

logger = logging.getLogger()


class Evaluation(BaseModel):
    feedback: str = Field(
        description="Tu feedback sobre el informe financiero y la justificación de tu puntuación"
    )
    score: float = Field(
        description="Puntuación de 0 a 100 donde 0 representa un informe financiero de calidad terrible y 100 representa un informe financiero sobresaliente"
    )


async def evaluate(original_instructions, original_task, original_output) -> Evaluation:
    # Obtener configuración del modelo
    model_id = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-3-7-sonnet-20250219-v1:0")
    # Establecer región para llamadas LiteLLM Bedrock
    bedrock_region = os.getenv("BEDROCK_REGION", "us-west-2")
    logger.info(f"DEBUG: BEDROCK_REGION from env = {bedrock_region}")
    os.environ["AWS_REGION_NAME"] = bedrock_region
    logger.info(f"DEBUG: Set AWS_REGION_NAME to {bedrock_region}")

    model = LitellmModel(model=f"bedrock/{model_id}")

    instructions = """
Eres un Agente de Evaluación que valora la calidad de un informe financiero generado por un agente de planificación financiera.
Se te proporcionarán las instrucciones enviadas al analista y su resultado, y debes evaluar la calidad del resultado.
"""

    # Crear task
    task = f"""
Al agente de planificación financiera se le dieron las siguientes instrucciones:

{original_instructions}

Y se le asignó esta tarea:

{original_task}

La salida del agente de planificación financiera fue:

{original_output}

Evalúa esta salida y responde con tus comentarios y puntuación.
"""

    try:
        logger.info("Evaluando informe financiero")
        agent = Agent(
            name="Judge Agent", instructions=instructions, model=model, output_type=Evaluation
        )
        result = await Runner.run(agent, input=task, max_turns=5)
        return result.final_output_as(Evaluation)
    except Exception as e:
        logger.error(f"Error al evaluar el informe financiero: {e}")
        return Evaluation(feedback=f"Error al evaluar el informe financiero: {e}", score=80)
