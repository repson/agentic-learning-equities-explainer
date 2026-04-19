"""
Script de prueba para ingestar documentos directamente a S3 Vectors.
Esto evita el API Gateway y prueba el servicio de S3 Vectors directamente.
"""

import os
import json
import boto3
import uuid
import datetime
from dotenv import load_dotenv
from pathlib import Path

# Cargar variables de entorno desde el directorio raíz del proyecto
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path, override=True)

# Obtener la configuración
VECTOR_BUCKET = os.getenv('VECTOR_BUCKET')
SAGEMAKER_ENDPOINT = os.getenv('SAGEMAKER_ENDPOINT', 'alex-embedding-endpoint')
INDEX_NAME = 'financial-research'

if not VECTOR_BUCKET:
    print("Error: Por favor ejecuta la Guía 3 Paso 4 para guardar VECTOR_BUCKET en .env")
    exit(1)

# Inicializar clientes de AWS
s3_vectors = boto3.client('s3vectors')
sagemaker_runtime = boto3.client('sagemaker-runtime')

def get_embedding(text):
    """Obtener vector de embedding desde el endpoint de SageMaker."""
    response = sagemaker_runtime.invoke_endpoint(
        EndpointName=SAGEMAKER_ENDPOINT,
        ContentType='application/json',
        Body=json.dumps({'inputs': text})
    )
    
    result = json.loads(response['Body'].read().decode())
    # HuggingFace devuelve un arreglo anidado [[[embedding]]], extraer el embedding real
    if isinstance(result, list) and len(result) > 0:
        if isinstance(result[0], list) and len(result[0]) > 0:
            if isinstance(result[0][0], list):
                return result[0][0]  # Extraer de [[[embedding]]]
            return result[0]  # Extraer de [[embedding]]
    return result  # Devolver tal cual si no está anidado

def ingest_document(text, metadata=None):
    """Ingestar un documento directamente en S3 Vectors."""
    # Obtener el embedding desde SageMaker
    print(f"Obteniendo embedding para el texto: {text[:100]}...")
    embedding = get_embedding(text)
    
    # Generar un ID único para el vector
    vector_id = str(uuid.uuid4())
    
    # Almacenar en S3 Vectors
    print(f"Guardando vector en el bucket: {VECTOR_BUCKET}, índice: {INDEX_NAME}")
    s3_vectors.put_vectors(
        vectorBucketName=VECTOR_BUCKET,
        indexName=INDEX_NAME,
        vectors=[{
            "key": vector_id,
            "data": {"float32": embedding},
            "metadata": {
                "text": text,
                "timestamp": datetime.datetime.utcnow().isoformat(),
                **(metadata or {})  # Incluir cualquier metadata adicional
            }
        }]
    )
    
    return vector_id

def main():
    """Probar ingesta directa en S3 Vectors."""
    
    print("Probando la Ingesta Directa en S3 Vectors")
    print("=" * 60)
    print(f"Bucket: {VECTOR_BUCKET}")
    print(f"Índice: {INDEX_NAME}")
    print(f"Modelo de Embedding: {SAGEMAKER_ENDPOINT}")
    print()
    
    # Documentos de prueba
    test_docs = [
        {
            'text': "Tesla Inc. (TSLA) es una empresa de vehículos eléctricos y energía limpia. Diseña, fabrica y vende vehículos eléctricos, sistemas de almacenamiento de energía y paneles solares.",
            'metadata': {
                'ticker': 'TSLA',
                'company_name': 'Tesla Inc.',
                'sector': 'Automotive/Energy',
                'source': 'portfolio'
            }
        },
        {
            'text': "Amazon.com Inc. (AMZN) es una compañía tecnológica multinacional centrada en comercio electrónico, computación en la nube (AWS), streaming digital e inteligencia artificial.",
            'metadata': {
                'ticker': 'AMZN',
                'company_name': 'Amazon.com Inc.',
                'sector': 'Technology/Retail',
                'source': 'portfolio'
            }
        },
        {
            'text': "NVIDIA Corporation (NVDA) diseña unidades de procesamiento gráfico (GPU) para juegos y mercados profesionales, así como unidades de sistema en chip para computación móvil y automoción.",
            'metadata': {
                'ticker': 'NVDA',
                'company_name': 'NVIDIA Corporation',
                'sector': 'Technology/Semiconductors',
                'source': 'portfolio'
            }
        }
    ]
    
    # Ingestar cada documento
    for i, doc in enumerate(test_docs, 1):
        print(f"Ingestando documento {i}: {doc['metadata'].get('ticker', 'Desconocido')}")
        try:
            doc_id = ingest_document(doc['text'], doc['metadata'])
            print(f"  ✓ ¡Éxito! ID del documento: {doc_id}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
        print()
    
    print("¡Prueba completada!")
    print("\nTu base de conocimiento S3 Vectors ahora contiene información sobre:")
    for doc in test_docs:
        print(f"  - {doc['metadata']['company_name']} ({doc['metadata']['ticker']})")
    
    print("\n⏱️  Nota: Las actualizaciones en S3 Vectors están disponibles inmediatamente.")
    print("   ¡Puedes ejecutar test_search_s3vectors.py ahora mismo para buscar!")

if __name__ == "__main__":
    main()