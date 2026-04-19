"""
Módulo de observabilidad para la integración con LangFuse.
Proporciona un gestor de contexto sencillo para configurar y vaciar trazas.
"""

import os
import logging
from contextlib import contextmanager

# Usar el logger raíz por compatibilidad con Lambda
logger = logging.getLogger()
logger.setLevel(logging.INFO)


@contextmanager
def observe():
    """
    Gestor de contexto para la observabilidad con LangFuse.

    Configura la observabilidad de LangFuse si las variables de entorno están configuradas,
    y asegura que las trazas se vacíen al salir.

    Uso:
        from observability import observe

        with observe():
            # Tu código que usa OpenAI Agents SDK
            result = await agent.run(...)
    """
    logger.info("🔍 Observabilidad: Comprobando configuración...")

    # Verifica si existen las variables de entorno requeridas
    has_langfuse = bool(os.getenv("LANGFUSE_SECRET_KEY"))
    has_openai = bool(os.getenv("OPENAI_API_KEY"))

    logger.info(f"🔍 Observabilidad: Existe LANGFUSE_SECRET_KEY: {has_langfuse}")
    logger.info(f"🔍 Observabilidad: Existe OPENAI_API_KEY: {has_openai}")

    if not has_langfuse:
        logger.info("🔍 Observabilidad: LangFuse no está configurado, omitiendo la configuración")
        yield
        return

    if not has_openai:
        logger.warning("⚠️  Observabilidad: OPENAI_API_KEY no está configurada, las trazas pueden no exportarse")

    # Variable local para el cliente (no es necesario global)
    langfuse_client = None

    # Intentar configurar LangFuse
    try:
        logger.info("🔍 Observabilidad: Configurando LangFuse...")

        import logfire
        from langfuse import get_client

        # Configurar logfire para instrumentar OpenAI Agents SDK
        logfire.configure(
            service_name="alex_retirement_agent",
            send_to_logfire=False,  # No enviar a Logfire cloud
        )
        logger.info("✅ Observabilidad: Logfire configurado")

        # Instrumentar OpenAI Agents SDK
        logfire.instrument_openai_agents()
        logger.info("✅ Observabilidad: OpenAI Agents SDK instrumentado")

        # Inicializar cliente de LangFuse
        langfuse_client = get_client()
        logger.info("✅ Observabilidad: Cliente de LangFuse inicializado")

        # Opcional: Comprobar autenticación (llamada bloqueante, usar con moderación)
        try:
            auth_result = langfuse_client.auth_check()
            logger.info(
                f"✅ Observabilidad: Comprobación de autenticación de LangFuse pasada (resultado: {auth_result})"
            )
        except Exception as auth_error:
            logger.warning(f"⚠️  Observabilidad: Falló la comprobación de autenticación pero se continúa: {auth_error}")

        logger.info("🎯 Observabilidad: Configuración completa - las trazas se enviarán a LangFuse")

    except ImportError as e:
        logger.error(f"❌ Observabilidad: Falta un paquete requerido: {e}")
        langfuse_client = None
    except Exception as e:
        logger.error(f"❌ Observabilidad: Falló la configuración: {e}")
        langfuse_client = None

    try:
        # Ceder el control de vuelta al código que llama
        yield
    finally:
        # Vaciar trazas al salir
        if langfuse_client:
            try:
                logger.info("🔍 Observabilidad: Vaciando trazas a LangFuse...")
                langfuse_client.flush()
                langfuse_client.shutdown()

                # Añade un retraso de 10 segundos para asegurar que las peticiones de red se completen
                # Esto es un workaround para la terminación inmediata de Lambda
                import time

                logger.info("🔍 Observabilidad: Esperando 10 segundos para completar el vaciado...")
                time.sleep(10)

                logger.info("✅ Observabilidad: Trazas vaciadas correctamente")
            except Exception as e:
                logger.error(f"❌ Observabilidad: Error al vaciar las trazas: {e}")
        else:
            logger.debug("🔍 Observabilidad: No hay cliente para vaciar")
