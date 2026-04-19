"""
Función Lambda para buscar en S3 Vectors.
"""

import json
import os
import boto3

# Variables de entorno
VECTOR_BUCKET = os.environ.get('VECTOR_BUCKET', 'alex-vectors')
SAGEMAKER_ENDPOINT = os.environ.get('SAGEMAKER_ENDPOINT')
INDEX_NAME = os.environ.get('INDEX_NAME', 'financial-research')

# Inicializar clientes de AWS
sagemaker_runtime = boto3.client('sagemaker-runtime')
s3_vectors = boto3.client('s3vectors')


def get_embedding(text):
    """Obtiene el vector de embedding desde el endpoint de SageMaker."""
    response = sagemaker_runtime.invoke_endpoint(
        EndpointName=SAGEMAKER_ENDPOINT,
        ContentType='application/json',
        Body=json.dumps({'inputs': text})
    )
    
    result = json.loads(response['Body'].read().decode())
    # HuggingFace devuelve un array anidado [[[embedding]]], extrae el embedding real
    if isinstance(result, list) and len(result) > 0:
        if isinstance(result[0], list) and len(result[0]) > 0:
            if isinstance(result[0][0], list):
                return result[0][0]  # Extrae de [[[embedding]]]
            return result[0]  # Extrae de [[embedding]]
    return result  # Devuelve tal cual si no está anidado


def lambda_handler(event, context):
    """
    Manejador de búsqueda.
    Espera un body JSON con:
    {
        "query": "Texto de búsqueda",
        "k": 5  # Opcional, por defecto 5
    }
    """
    # Parsear el body de la petición
    if isinstance(event.get('body'), str):
        body = json.loads(event['body'])
    else:
        body = event.get('body', {})
    
    query_text = body.get('query')
    k = body.get('k', 5)
    
    if not query_text:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Falta el campo requerido: query'})
        }
    
    # Obtener embedding para la consulta
    print(f"Obteniendo embedding para la consulta: {query_text}")
    query_embedding = get_embedding(query_text)
    
    # Buscar en S3 Vectors
    print(f"Buscando en bucket: {VECTOR_BUCKET}, índice: {INDEX_NAME}")
    response = s3_vectors.query_vectors(
        vectorBucketName=VECTOR_BUCKET,
        indexName=INDEX_NAME,
        queryVector={"float32": query_embedding},
        topK=k,
        returnDistance=True,
        returnMetadata=True
    )
    
    # Formatear resultados
    results = []
    for vector in response.get('vectors', []):
        results.append({
            'id': vector['key'],
            'score': vector.get('distance', 0),
            'text': vector.get('metadata', {}).get('text', ''),
            'metadata': vector.get('metadata', {})
        })
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'results': results,
            'count': len(results)
        })
    }