"""
Función Lambda para disparar el endpoint de investigación de App Runner.
Llamada por EventBridge en un horario programado.
"""
import os
import urllib.request
import json


def handler(event, context):
    """Dispara el endpoint de investigación en App Runner."""
    
    app_runner_url = os.environ.get('APP_RUNNER_URL')
    if not app_runner_url:
        raise ValueError("La variable de entorno APP_RUNNER_URL no está configurada")
    
    # Eliminar cualquier protocolo si está incluido
    if app_runner_url.startswith('https://'):
        app_runner_url = app_runner_url.replace('https://', '')
    elif app_runner_url.startswith('http://'):
        app_runner_url = app_runner_url.replace('http://', '')
    
    url = f"https://{app_runner_url}/research"
    
    try:
        # Crear una petición POST con body JSON vacío (el agente elegirá el tema)
        data = json.dumps({}).encode('utf-8')
        req = urllib.request.Request(
            url, 
            data=data,
            method='POST',
            headers={'Content-Type': 'application/json'}
        )
        
        with urllib.request.urlopen(req, timeout=180) as response:
            result = response.read().decode('utf-8')
            print(f"Investigación disparada correctamente: {result}")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Investigación disparada correctamente',
                    'result': result
                })
            }
    except Exception as e:
        print(f"Error al disparar la investigación: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }