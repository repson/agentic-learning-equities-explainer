"""
Script de prueba para buscar en S3 Vectors.
Esto demuestra cómo buscar los documentos indexados.
"""

import os
import json
import boto3
from dotenv import load_dotenv
from pathlib import Path

# Cargar las variables de entorno desde la raíz del proyecto
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path, override=True)

# Obtener la configuración
VECTOR_BUCKET = os.getenv('VECTOR_BUCKET')
SAGEMAKER_ENDPOINT = os.getenv('SAGEMAKER_ENDPOINT', 'alex-embedding-endpoint')
INDEX_NAME = 'financial-research'

if not VECTOR_BUCKET:
    print("Error: Por favor, ejecuta la Guía 3 Paso 4 para guardar VECTOR_BUCKET en .env")
    exit(1)

# Inicializar los clientes de AWS
s3_vectors = boto3.client('s3vectors')
sagemaker_runtime = boto3.client('sagemaker-runtime')

def get_embedding(text):
    """Obtener el vector de embedding desde el endpoint de SageMaker."""
    response = sagemaker_runtime.invoke_endpoint(
        EndpointName=SAGEMAKER_ENDPOINT,
        ContentType='application/json',
        Body=json.dumps({'inputs': text})
    )
    
    result = json.loads(response['Body'].read().decode())
    # HuggingFace retorna un array anidado [[[embedding]]], extraer el embedding real
    if isinstance(result, list) and len(result) > 0:
        if isinstance(result[0], list) and len(result[0]) > 0:
            if isinstance(result[0][0], list):
                return result[0][0]  # Extraer de [[[embedding]]]
            return result[0]  # Extraer de [[embedding]]
    return result  # Retornar tal cual si no está anidado

def list_all_vectors():
    """Listar todos los vectores en el índice."""
    print(f"Listando vectores en el bucket: {VECTOR_BUCKET}, índice: {INDEX_NAME}")
    print("=" * 60)
    
    try:
        # S3 Vectors no tiene una operación directa de listado, así que haremos una búsqueda amplia
        # Buscar un término común para obtener algunos resultados
        test_embedding = get_embedding("company")
        
        response = s3_vectors.query_vectors(
            vectorBucketName=VECTOR_BUCKET,
            indexName=INDEX_NAME,
            queryVector={"float32": test_embedding},
            topK=10,
            returnDistance=True,
            returnMetadata=True
        )
        
        vectors = response.get('vectors', [])
        print(f"\nSe encontraron {len(vectors)} vectores en el índice:\n")
        
        for i, vector in enumerate(vectors, 1):
            metadata = vector.get('metadata', {})
            text_preview = metadata.get('text', '')[:100] + '...' if len(metadata.get('text', '')) > 100 else metadata.get('text', '')
            
            print(f"{i}. ID del Vector: {vector['key']}")
            if metadata.get('ticker'):
                print(f"   Ticker: {metadata['ticker']}")
            if metadata.get('company_name'):
                print(f"   Compañía: {metadata['company_name']}")
            if metadata.get('sector'):
                print(f"   Sector: {metadata['sector']}")
            print(f"   Texto: {text_preview}")
            print()
            
    except Exception as e:
        print(f"Error al listar los vectores: {e}")

def search_vectors(query_text, k=5):
    """Buscar vectores por texto de consulta."""
    print(f"\nBuscando: '{query_text}'")
    print("-" * 40)
    
    try:
        # Obtener embedding para la consulta
        query_embedding = get_embedding(query_text)
        
        # Buscar en S3 Vectors
        response = s3_vectors.query_vectors(
            vectorBucketName=VECTOR_BUCKET,
            indexName=INDEX_NAME,
            queryVector={"float32": query_embedding},
            topK=k,
            returnDistance=True,
            returnMetadata=True
        )
        
        vectors = response.get('vectors', [])
        print(f"Se encontraron {len(vectors)} resultados:\n")
        
        for vector in vectors:
            metadata = vector.get('metadata', {})
            distance = vector.get('distance', 0)
            
            print(f"Puntuación: {1 - distance:.3f}")  # Convertir distancia a puntuación de similitud
            if metadata.get('company_name'):
                print(f"Compañía: {metadata['company_name']} ({metadata.get('ticker', 'N/A')})")
            print(f"Texto: {metadata.get('text', '')[:200]}...")
            print()
            
    except Exception as e:
        print(f"Error al buscar: {e}")

def main():
    """Explorar la base de datos de S3 Vectors."""
    print("=" * 60)
    print("Explorador de la Base de Datos Alex S3 Vectors")
    print("=" * 60)
    print(f"Bucket: {VECTOR_BUCKET}")
    print(f"Índice: {INDEX_NAME}")
    print()
    
    # Listar todos los vectores
    list_all_vectors()
    
    # Búsquedas de ejemplo
    print("=" * 60)
    print("Búsquedas Semánticas de Ejemplo")
    print("=" * 60)
    
    # Buscar conceptos específicos
    search_queries = [
        "vehículos eléctricos y transporte sostenible",
        "computación en la nube y servicios AWS",
        "inteligencia artificial y computación GPU"
    ]
    
    for query in search_queries:
        search_vectors(query, k=3)
    
    print("\n✨ S3 Vectors ofrece búsqueda semántica - observa cómo encuentra")
    print("   documentos conceptualmente relacionados incluso con palabras diferentes!")

if __name__ == "__main__":
    main()