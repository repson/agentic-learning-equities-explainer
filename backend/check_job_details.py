from database.src import Database
import json

db = Database()

# Obtener los jobs completados más recientes
jobs = db.jobs.find_all()
sorted_jobs = sorted(jobs, key=lambda x: x['created_at'], reverse=True)

# Buscar el primer job completado
completed_job = None
for job in sorted_jobs:
    if job['status'] == 'completed':
        completed_job = job
        break

if completed_job:
    print(f"Examinando job: {completed_job['id']}")
    print(f"Estado: {completed_job['status']}")
    print(f"Creado: {completed_job['created_at']}")
    print(f"Actualizado: {completed_job.get('updated_at', 'N/A')}")

    # Revisar todos los campos
    for key, value in completed_job.items():
        if key == 'results':
            if value:
                print(f"\n{key}: Presente")
                try:
                    results = json.loads(value) if isinstance(value, str) else value
                    print(f"  Claves en results: {list(results.keys())}")
                    for r_key in results:
                        if isinstance(results[r_key], str):
                            print(f"    {r_key}: {len(results[r_key])} caracteres")
                        elif isinstance(results[r_key], list):
                            print(f"    {r_key}: {len(results[r_key])} elementos")
                        elif isinstance(results[r_key], dict):
                            print(f"    {r_key}: diccionario con claves {list(results[r_key].keys())}")
                except Exception as e:
                    print(f"  Error al analizar results: {e}")
                    print(f"  Tipo de valor crudo: {type(value)}")
                    print(f"  Valor crudo (primeros 500 caracteres): {str(value)[:500]}")
            else:
                print(f"\n{key}: Ninguno/Vacío")
        elif key not in ['id', 'status', 'created_at', 'updated_at']:
            if value:
                value_str = str(value)
                if len(value_str) > 100:
                    print(f"{key}: {value_str[:100]}...")
                else:
                    print(f"{key}: {value_str}")
else:
    print("No se encontraron jobs completados")