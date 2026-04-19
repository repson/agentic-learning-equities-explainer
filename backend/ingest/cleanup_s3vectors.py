"""
Limpia la base de datos de vectores S3 eliminando todos los datos de prueba.
Este script accede directamente a S3 Vectors sin pasar por API Gateway.
"""

import os
import json
import boto3
from dotenv import load_dotenv
from pathlib import Path

# Cargar variables de entorno desde la raíz del proyecto
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path, override=True)

# Obtener configuración
VECTOR_BUCKET = os.getenv('VECTOR_BUCKET')
INDEX_NAME = 'financial-research'

if not VECTOR_BUCKET:
    print("Error: VECTOR_BUCKET no encontrado en .env")
    exit(1)

# Inicializar cliente de S3 Vectors
s3_vectors = boto3.client('s3vectors')

def delete_all_vectors():
    """Elimina todos los vectores del índice."""
    print("Limpiando la base de datos de S3 Vectors...")
    print(f"Bucket: {VECTOR_BUCKET}")
    print(f"Índice: {INDEX_NAME}")
    print()
    
    deleted_count = 0
    
    try:
        # S3 Vectors no tiene una operación de lista, así que hay que buscar ampliamente
        print("Buscando vectores para eliminar...")
        
        # Conseguir un embedding real para un término de búsqueda genérico
        sagemaker_runtime = boto3.client('sagemaker-runtime')
        SAGEMAKER_ENDPOINT = os.getenv('SAGEMAKER_ENDPOINT', 'alex-embedding-endpoint')
        
        response = sagemaker_runtime.invoke_endpoint(
            EndpointName=SAGEMAKER_ENDPOINT,
            ContentType='application/json',
            Body='{"inputs": "document"}'
        )
        
        result = json.loads(response['Body'].read().decode())
        # Extraer del array anidado [[[embedding]]]
        dummy_vector = result[0][0]
        
        # S3 Vectors limita topK a 30, así que hay que iterar
        all_vectors = []
        batch_size = 30
        
        while True:
            response = s3_vectors.query_vectors(
                vectorBucketName=VECTOR_BUCKET,
                indexName=INDEX_NAME,
                queryVector={"float32": dummy_vector},
                topK=batch_size,
                returnMetadata=True
            )
            
            vectors = response.get('vectors', [])
            if not vectors:
                break
                
            all_vectors.extend(vectors)
            
            # Eliminar este lote antes de obtener más
            print(f"  Lote encontrado de {len(vectors)} vectores...")
            for vector in vectors:
                try:
                    s3_vectors.delete_vectors(
                        vectorBucketName=VECTOR_BUCKET,
                        indexName=INDEX_NAME,
                        keys=[vector['key']]
                    )
                    deleted_count += 1
                except Exception as e:
                    print(f"  Error eliminando {vector['key']}: {e}")
            
            # Si recibimos menos de batch_size, hemos terminado
            if len(vectors) < batch_size:
                break
        
        if deleted_count > 0:
            print(f"\n✅ Se eliminaron correctamente {deleted_count} vectores")
        else:
            print("✅ No se encontraron vectores - la base de datos ya está vacía")
            
    except Exception as e:
        print(f"❌ Error durante la limpieza: {e}")
        if deleted_count > 0:
            print(f"   (Parcialmente exitoso - se eliminaron {deleted_count} vectores)")

def main():
    """Limpia la base de datos de vectores S3."""
    print("=" * 60)
    print("Limpieza de la base de datos de S3 Vectors")
    print("=" * 60)
    print()
    
    # Confirmar antes de eliminar
    response = input("⚠️  Esto ELIMINARÁ TODOS los vectores. ¿Continuar? (yes/no): ")
    if response.lower() != 'yes':
        print("Limpieza cancelada.")
        return
    
    print()
    delete_all_vectors()
    
    print("\n💡 Consejo: Ejecuta test_api.py para añadir nuevos datos de prueba")

if __name__ == "__main__":
    main()