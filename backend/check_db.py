from database.src import Database

db = Database()
print("Comprobando precios de los instrumentos...")
instruments = db.instruments.find_all()
print(f"Encontrados {len(instruments)} instrumentos")
for inst in instruments:
    price = inst.get("current_price")
    symbol = inst.get("symbol")
    if price:
        price_val = float(price) if isinstance(price, str) else price
        print(f"  {symbol}: ${price_val:.2f}")
    else:
        print(f"  {symbol}: N/D")

print("\nComprobando trabajos recientes...")
jobs = db.jobs.find_all()
print(f"Encontrados {len(jobs)} trabajos en total")

# Ordenar los trabajos por created_at y mostrar los últimos 5
sorted_jobs = sorted(jobs, key=lambda x: x['created_at'], reverse=True)[:5]
for job in sorted_jobs:
    print(f"  Trabajo {job['id'][:8]}...: {job['status']} - {job['created_at']}")
    if job.get('results'):
        print(f"    Tiene resultados: Sí (longitud: {len(str(job['results']))} caracteres)")
        # Comprobar si son datos JSON
        import json
        try:
            results = json.loads(job['results']) if isinstance(job['results'], str) else job['results']
            if 'charter' in results:
                print(f"    Datos de charter: {len(results['charter'])} gráficas")
        except:
            pass
    else:
        print(f"    Tiene resultados: No")