"""
Función Lambda para ingestar texto en S3 Vectors con embeddings.
"""

import json
import os
import boto3
import datetime
import uuid

# Variables de entorno
VECTOR_BUCKET = os.environ.get('VECTOR_BUCKET', 'alex-vectors')
SAGEMAKER_ENDPOINT = os.environ.get('SAGEMAKER_ENDPOINT')
INDEX_NAME = os.environ.get('INDEX_NAME', 'financial-research')

# Inicializar clientes de AWS
sagemaker_runtime = boto3.client('sagemaker-runtime')
s3_vectors = boto3.client('s3vectors')


def get_embedding(text):
    """Obtiene el vector embedding desde el endpoint de SageMaker."""
    response = sagemaker_runtime.invoke_endpoint(
        EndpointName=SAGEMAKER_ENDPOINT,
        ContentType='application/json',
        Body=json.dumps({'inputs': text})
    )
    
    result = json.loads(response['Body'].read().decode())
    # HuggingFace devuelve un array anidado [[[embedding]]], extraer el embedding real
    if isinstance(result, list) and len(result) > 0:
        if isinstance(result[0], list) and len(result[0]) > 0:
            if isinstance(result[0][0], list):
                return result[0][0]  # Extrae de [[[embedding]]]
            return result[0]  # Extrae de [[embedding]]
    return result  # Retorna tal cual si no está anidado


def lambda_handler(event, context):
    """
    Handler principal de Lambda.
    Espera un cuerpo JSON con:
    {
        "text": "Texto a ingestar",
        "metadata": {
            "source": "fuente opcional",
            "category": "categoría opcional"
        }
    }
    """
    try:
        # Parsear el cuerpo de la petición
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        text = body.get('text')
        metadata = body.get('metadata', {})
        
        if not text:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Falta el campo requerido: text'})
            }
        
        # Obtener embedding desde SageMaker
        print(f"Obteniendo embedding para el texto: {text[:100]}...")
        embedding = get_embedding(text)
        
        # Generar ID único para el vector
        vector_id = str(uuid.uuid4())
        
        # Guardar en S3 Vectors
        print(f"Guardando vector en bucket: {VECTOR_BUCKET}, índice: {INDEX_NAME}")
        s3_vectors.put_vectors(
            vectorBucketName=VECTOR_BUCKET,
            indexName=INDEX_NAME,
            vectors=[{
                "key": vector_id,
                "data": {"float32": embedding},
                "metadata": {
                    "text": text,
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                    **metadata  # Incluir cualquier metadata adicional
                }
            }]
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Documento indexado correctamente',
                'document_id': vector_id
            })
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }