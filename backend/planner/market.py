"""
Funciones de datos de mercado usando polygon.io para obtener precios en tiempo real.
"""

import logging
from typing import Set
from prices import get_share_price

logger = logging.getLogger()


def update_instrument_prices(job_id: str, db) -> None:
    """
    Obtiene los precios actuales de todos los instrumentos en la cartera del usuario usando polygon.io.
    Actualiza la tabla instruments con los precios actuales.

    Args:
        job_id: El ID del trabajo para identificar la cartera del usuario
        db: Instancia de la base de datos
    """
    try:
        logger.info(f"Mercado: Obteniendo precios actuales para el trabajo {job_id}")

        # Obtiene el trabajo para encontrar el usuario
        job = db.jobs.find_by_id(job_id)
        if not job:
            logger.error(f"Mercado: Trabajo {job_id} no encontrado")
            return

        user_id = job['clerk_user_id']

        # Obtiene todos los símbolos únicos de las posiciones del usuario
        accounts = db.accounts.find_by_user(user_id)
        symbols = set()

        for account in accounts:
            positions = db.positions.find_by_account(account['id'])
            for position in positions:
                symbols.add(position['symbol'])

        if not symbols:
            logger.info("Mercado: No hay símbolos para actualizar precios")
            return

        logger.info(f"Mercado: Obteniendo precios para {len(symbols)} símbolos: {symbols}")

        # Actualiza los precios para cada símbolo
        update_prices_for_symbols(symbols, db)

        logger.info("Mercado: Actualización de precios completada")

    except Exception as e:
        logger.error(f"Mercado: Error actualizando los precios de los instrumentos: {e}")
        # Error no crítico, continuar con el análisis


def update_prices_for_symbols(symbols: Set[str], db) -> None:
    """
    Obtiene y actualiza los precios para un conjunto de símbolos utilizando polygon.io.

    Args:
        symbols: Conjunto de símbolos de cotización para actualizar
        db: Instancia de la base de datos
    """
    if not symbols:
        logger.info("Mercado: No hay símbolos para actualizar")
        return

    symbols_list = list(symbols)
    price_map = {}

    # Obtiene el precio para cada símbolo usando polygon.io
    for symbol in symbols_list:
        try:
            price = get_share_price(symbol)
            if price > 0:
                price_map[symbol] = price
                logger.info(f"Mercado: Se obtuvo el precio de {symbol}: ${price:.2f}")
            else:
                logger.warning(f"Mercado: No hay precio disponible para {symbol}")
        except Exception as e:
            logger.warning(f"Mercado: No se pudo obtener el precio para {symbol}: {e}")

    logger.info(f"Mercado: Se obtuvieron precios para {len(price_map)}/{len(symbols_list)} símbolos")

    # Actualiza la base de datos con los precios obtenidos
    for symbol, price in price_map.items():
        try:
            instrument = db.instruments.find_by_symbol(symbol)
            if instrument:
                update_data = {'current_price': price}
                success = db.client.update(
                    'instruments',
                    update_data,
                    "symbol = :symbol",
                    {'symbol': symbol}
                )
                if success:
                    logger.info(f"Mercado: Se actualizó el precio de {symbol} a ${price:.2f}")
                else:
                    logger.warning(f"Mercado: Falló la actualización del precio para {symbol}")
            else:
                logger.warning(f"Mercado: Instrumento {symbol} no encontrado en la base de datos")
        except Exception as e:
            logger.error(f"Mercado: Error actualizando {symbol} en la base de datos: {e}")

    # Registra los símbolos que no obtuvieron precio
    missing = set(symbols_list) - set(price_map.keys())
    if missing:
        logger.warning(f"Mercado: No se encontraron precios para: {missing}")


def get_all_portfolio_symbols(db) -> Set[str]:
    """
    Obtiene todos los símbolos únicos entre las carteras de todos los usuarios.
    Útil para pre-obtener precios en operaciones en lote.

    Args:
        db: Instancia de la base de datos

    Returns:
        Conjunto de símbolos únicos de cotización
    """
    symbols = set()

    try:
        # Obtiene todas las posiciones (esto puede necesitar paginación para grandes conjuntos de datos)
        all_positions = db.db.execute(
            "SELECT DISTINCT symbol FROM positions"
        )

        for position in all_positions:
            if position['symbol']:
                symbols.add(position['symbol'])

    except Exception as e:
        logger.error(f"Mercado: Error obteniendo todos los símbolos: {e}")

    return symbols