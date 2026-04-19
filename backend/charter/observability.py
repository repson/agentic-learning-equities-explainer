"""
Módulo de observabilidad para la integración con LangFuse.
Proporciona un gestor de contexto sencillo para configurar y vaciar trazas.
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
    Gestor de contexto para observabilidad con LangFuse.

    Configura la observabilidad de LangFuse si las variables de entorno están configuradas,
    y asegura que las trazas se vacíen al salir.

    Uso:
        from observability import observe

        with observe():
            # Tu código que utiliza el SDK de OpenAI Agents
            result = await agent.run(...)
    """
    logger.info("🔍 Observabilidad: Comprobando configuración...")

    # Comprobar si existen las variables de entorno requeridas
    has_langfuse = bool(os.getenv("LANGFUSE_SECRET_KEY"))
    has_openai = bool(os.getenv("OPENAI_API_KEY"))

    logger.info(f"🔍 Observabilidad: LANGFUSE_SECRET_KEY existe: {has_langfuse}")
    logger.info(f"🔍 Observabilidad: OPENAI_API_KEY existe: {has_openai}")

    if not has_langfuse:
        logger.info("🔍 Observabilidad: LangFuse no está configurado, omitiendo configuración")
        yield
        return

    if not has_openai:
        logger.warning("⚠️  Observabilidad: OPENAI_API_KEY no configurado, las trazas pueden no exportarse")

    # Variable local para el cliente (no se necesita global)
    langfuse_client = None

    # Intentar configurar LangFuse
    try:
        logger.info("🔍 Observabilidad: Configurando LangFuse...")

        import logfire
        from langfuse import get_client

        # Configurar logfire para instrumentar el SDK de OpenAI Agents
        logfire.configure(
            service_name="alex_charter_agent",
            send_to_logfire=False,  # No enviar a la nube de Logfire
        )
        logger.info("✅ Observabilidad: Logfire configurado")

        # Instrumentar el SDK de OpenAI Agents
        logfire.instrument_openai_agents()
        logger.info("✅ Observabilidad: SDK de OpenAI Agents instrumentado")

        # Inicializar el cliente de LangFuse
        langfuse_client = get_client()
        logger.info("✅ Observabilidad: Cliente de LangFuse inicializado")

        # Opcional: Comprobar autenticación (llamada bloqueante, usar con precaución)
        try:
            auth_result = langfuse_client.auth_check()
            logger.info(
                f"✅ Observabilidad: Comprobación de autenticación de LangFuse exitosa (resultado: {auth_result})"
            )
        except Exception as auth_error:
            logger.warning(f"⚠️  Observabilidad: La comprobación de autenticación falló pero se continúa: {auth_error}")

        logger.info("🎯 Observabilidad: Configuración completa - las trazas se enviarán a LangFuse")

    except ImportError as e:
        logger.error(f"❌ Observabilidad: Falta un paquete requerido: {e}")
        langfuse_client = None
    except Exception as e:
        logger.error(f"❌ Observabilidad: Fallo en la configuración: {e}")
        langfuse_client = None

    try:
        # Devolver el control al código que llama
        yield
    finally:
        # Vaciar trazas al salir
        if langfuse_client:
            try:
                logger.info("🔍 Observabilidad: Vaciando trazas a LangFuse...")
                langfuse_client.flush()
                langfuse_client.shutdown()

                # Añadir una espera de 10 segundos para asegurar que se completen las solicitudes de red
                # Esto es un parche para la terminación inmediata de Lambda
                import time

                logger.info("🔍 Observabilidad: Esperando 10 segundos para completar el vaciado de trazas...")
                time.sleep(10)

                logger.info("✅ Observabilidad: Trazas vaciadas exitosamente")
            except Exception as e:
                logger.error(f"❌ Observabilidad: Fallo al vaciar las trazas: {e}")
        else:
            logger.debug("🔍 Observabilidad: No hay cliente para vaciar")
