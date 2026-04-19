"""
Test de obtención de datos de mercado
"""

from src import Database
from market import update_instrument_prices

def test_market():
    db = Database()

    # Buscar un usuario con posiciones
    user_id = 'user_30BmVRQvPMVcGt9kWAH4BOy5Cjy'

    # Crear un job de prueba
    job_id = db.jobs.create_job(
        clerk_user_id=user_id,
        job_type='test_market',
        request_payload={'test': True}
    )

    print(f"Probando la obtención de datos de mercado para el job {job_id}")

    # Obtener precios iniciales
    accounts = db.accounts.find_by_user(user_id)
    symbols = set()
    for account in accounts:
        positions = db.positions.find_by_account(account['id'])
        for position in positions:
            symbols.add(position['symbol'])
            instrument = db.instruments.find_by_symbol(position['symbol'])
            if instrument:
                print(f"  {position['symbol']}: Precio actual = ${instrument.get('current_price')}")

    print(f"\nObteniendo precios para {len(symbols)} símbolos...")

    # Actualizar precios
    update_instrument_prices(job_id, db)

    print("\nDespués de la actualización:")
    # Comprobar los precios actualizados
    for symbol in symbols:
        instrument = db.instruments.find_by_symbol(symbol)
        if instrument:
            print(f"  {symbol}: Precio actual = ${instrument.get('current_price')}")

    # Limpiar
    db.jobs.delete(job_id)
    print(f"\nJob de prueba {job_id} eliminado")

if __name__ == "__main__":
    test_market()