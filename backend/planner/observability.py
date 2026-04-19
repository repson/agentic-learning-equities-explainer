"""
Módulo de observabilidad para la integración con LangFuse.
Proporciona un context manager sencillo para configurar y finalizar el envío de trazas.
"""

import os
import logging
from contextlib import contextmanager

# Usar el logger raíz para compatibilidad con Lambda
logger = logging.getLogger()
logger.setLevel(logging.INFO)


@contextmanager
def observe():
    """
    Context manager para observabilidad con LangFuse.

    Configura la observabilidad de LangFuse si las variables de entorno están configuradas,
    y asegura que las trazas se envíen al salir.

    Uso:
        from observability import observe

        with observe():
            # Tu código que usa OpenAI Agents SDK
            result = await agent.run(...)
    """
    logger.info("🔍 Observabilidad: Comprobando configuración...")

    # Comprobar si existen las variables de entorno requeridas
    has_langfuse = bool(os.getenv("LANGFUSE_SECRET_KEY"))
    has_openai = bool(os.getenv("OPENAI_API_KEY"))

    logger.info(f"🔍 Observabilidad: LANGFUSE_SECRET_KEY existe: {has_langfuse}")
    logger.info(f"🔍 Observabilidad: OPENAI_API_KEY existe: {has_openai}")

    if not has_langfuse:
        logger.info("🔍 Observabilidad: LangFuse no está configurado, omitiendo inicialización")
        yield
        return

    if not has_openai:
        logger.warning("⚠️  Observabilidad: OPENAI_API_KEY no está definida, puede que las trazas no se exporten")

    # Variable local para el cliente (no es necesario global)
    langfuse_client = None

    # Intentar configurar LangFuse
    try:
        logger.info("🔍 Observabilidad: Configurando LangFuse...")

        import logfire
        from langfuse import get_client

        # Configurar logfire para instrumentar el SDK de OpenAI Agents
        logfire.configure(
            service_name="alex_planner_agent",
            send_to_logfire=False,  # No enviar a la nube de Logfire
        )
        logger.info("✅ Observabilidad: Logfire configurado")

        # Instrumentar el SDK de OpenAI Agents
        logfire.instrument_openai_agents()
        logger.info("✅ Observabilidad: SDK OpenAI Agents instrumentado")

        # Inicializar el cliente de LangFuse
        langfuse_client = get_client()
        logger.info("✅ Observabilidad: Cliente de LangFuse inicializado")

        # Opcional: comprobar autenticación (llamada bloqueante, usar con precaución)
        try:
            auth_result = langfuse_client.auth_check()
            logger.info(
                f"✅ Observabilidad: Comprobación de autenticación de LangFuse correcta (resultado: {auth_result})"
            )
        except Exception as auth_error:
            logger.warning(f"⚠️  Observabilidad: Error en comprobación de autenticación pero continuando: {auth_error}")

        logger.info("🎯 Observabilidad: Configuración completada - las trazas se enviarán a LangFuse")

    except ImportError as e:
        logger.error(f"❌ Observabilidad: Falta un paquete requerido: {e}")
        langfuse_client = None
    except Exception as e:
        logger.error(f"❌ Observabilidad: Fallo en la configuración: {e}")
        langfuse_client = None

    try:
        # Ceder el control al código que llama
        yield
    finally:
        # Enviar trazas al salir
        if langfuse_client:
            try:
                logger.info("🔍 Observabilidad: Enviando trazas a LangFuse...")
                langfuse_client.flush()
                langfuse_client.shutdown()

                # Añadir un retardo de 15 segundos para asegurar que las solicitudes de red se completen
                # Esto es un workaround para el cierre inmediato de Lambda
                import time

                logger.info("🔍 Observabilidad: Esperando 15 segundos para completar el envío de trazas...")
                time.sleep(15)

                logger.info("✅ Observabilidad: Trazas enviadas correctamente")
            except Exception as e:
                logger.error(f"❌ Observabilidad: Error al enviar las trazas: {e}")
        else:
            logger.debug("🔍 Observabilidad: No hay cliente para enviar")
