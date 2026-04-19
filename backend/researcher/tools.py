"""
Herramientas para el agente Alex Researcher
"""
import os
from typing import Dict, Any
from datetime import datetime, UTC
import httpx
from agents import function_tool
from tenacity import retry, stop_after_attempt, wait_exponential

# Configuración desde el entorno
ALEX_API_ENDPOINT = os.getenv("ALEX_API_ENDPOINT")
ALEX_API_KEY = os.getenv("ALEX_API_KEY")


def _ingest(document: Dict[str, Any]) -> Dict[str, Any]:
    """Función interna para realizar la llamada real a la API."""
    with httpx.Client() as client:
        response = client.post(
            ALEX_API_ENDPOINT,
            json=document,
            headers={"x-api-key": ALEX_API_KEY},
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10)
)
def ingest_with_retries(document: Dict[str, Any]) -> Dict[str, Any]:
    """Ingesta con lógica de reintento para cold starts de SageMaker."""
    return _ingest(document)


@function_tool
def ingest_financial_document(topic: str, analysis: str) -> Dict[str, Any]:
    """
    Ingresa un documento financiero en la base de conocimientos de Alex.
    
    Args:
        topic: El tema o asunto del análisis (por ejemplo, "Análisis de acciones de AAPL", "Guía de planificación de jubilación")
        analysis: Análisis detallado o consejo con datos e insights específicos
    
    Returns:
        Diccionario con el estado de éxito y el ID del documento
    """
    if not ALEX_API_ENDPOINT or not ALEX_API_KEY:
        return {
            "success": False,
            "error": "API de Alex no configurada. Ejecutando en modo local."
        }
    
    document = {
        "text": analysis,
        "metadata": {
            "topic": topic,
            "timestamp": datetime.now(UTC).isoformat()
        }
    }
    
    try:
        result = ingest_with_retries(document)
        return {
            "success": True,
            "document_id": result.get("document_id"),  # Cambiado de documentId
            "message": f"Análisis para {topic} ingresado correctamente"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }