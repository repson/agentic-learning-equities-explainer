# Infraestructura de Terraform

Este directorio contiene las configuraciones de Terraform para el proyecto Alex Financial Planner.

## Estructura

Cada parte del curso tiene su propio directorio independiente de Terraform:

- **`2_sagemaker/`** - Endpoint serverless de SageMaker para embeddings (Guía 2)
- **`3_ingestion/`** - S3 Vectors, Lambda y API Gateway para la ingestión de documentos (Guía 3)
- **`4_researcher/`** - Servicio App Runner para el agente investigador de IA (Guía 4)
- **`5_database/`** - Aurora Serverless v2 PostgreSQL con Data API (Guía 5)
- **`6_agents/`** - Funciones Lambda para la orquesta de agentes (Guía 6)
- **`7_frontend/`** - Lambda API y la infraestructura del frontend (Guía 7)
- **`8_observability/`** - Configuración de LangFuse y monitorización (Guía 8)

## Decisiones Clave de Diseño

### ¿Por qué directorios separados?

1. **Claridad educativa**: Cada guía corresponde exactamente a un directorio de Terraform
2. **Despliegue independiente**: Los estudiantes pueden desplegar cada parte sin afectar las demás
3. **Reducción de riesgo**: Errores en una parte no afectan la infraestructura desplegada anteriormente
4. **Aprendizaje progresivo**: No se pueden desplegar partes posteriores accidentalmente antes de completar las anteriores

### ¿Por qué estado local?

1. **Simplicidad**: No es necesario configurar ni gestionar un bucket S3 para el estado
2. **Cero dependencias**: Se puede comenzar a desplegar inmediatamente sin infraestructura previa
3. **Ahorro de costes**: No hay costes de almacenamiento S3 para los archivos de estado
4. **Seguridad**: Los archivos de estado están automáticamente en el .gitignore

## Uso

Para cada parte del curso:

```bash
# Navega al directorio específico de la parte
cd terraform/2_sagemaker  # (o 3_ingestion, 4_researcher, etc.)

# Inicializa Terraform (solo es necesario una vez por directorio)
terraform init

# Revisa lo que será creado
terraform plan

# Despliega la infraestructura
terraform apply

# Cuando termines con esa parte (opcional)
terraform destroy
```

## Variables de Entorno

Algunas configuraciones de Terraform requieren variables de entorno desde tu archivo `.env`:

- `OPENAI_API_KEY` - Para el agente investigador (Parte 4)
- `ALEX_API_ENDPOINT` - Endpoint de API Gateway (de la Parte 3)
- `ALEX_API_KEY` - Clave de API para ingestión (de la Parte 3)
- `AURORA_CLUSTER_ARN` - ARN del clúster Aurora (de la Parte 5)
- `AURORA_SECRET_ARN` - ARN de Secrets Manager (de la Parte 5)
- `VECTOR_BUCKET` - Nombre del bucket S3 Vectors (de la Parte 3)
- `BEDROCK_MODEL_ID` - Modelo Bedrock a utilizar (Parte 6)

## Gestión del Estado

- Cada directorio mantiene su propio archivo `terraform.tfstate`
- Los archivos de estado se almacenan localmente (no en S3)
- Todos los archivos `*.tfstate` están en el .gitignore por seguridad
- Haz una copia de seguridad de los archivos de estado antes de realizar cambios importantes

## Consideraciones para Producción

Esta estructura está optimizada para el aprendizaje. En producción, podrías considerar:

- **Estado remoto**: Almacenar el estado en S3 con locking de estado vía DynamoDB
- **Módulos**: Compartir configuraciones comunes entre entornos
- **Workspaces**: Gestionar múltiples entornos (dev, staging, prod)
- **CI/CD**: Pipelines de despliegue automatizados
- **Terragrunt**: Orquestar múltiples configuraciones de Terraform

## Resolución de Problemas

Si encuentras problemas:

1. **Conflictos de estado**: Cada directorio tiene estado independiente. Si necesitas importar recursos existentes:
   ```bash
   terraform import <resource_type>.<resource_name> <resource_id>
   ```

2. **Dependencias faltantes**: Asegúrate de haber completado las guías anteriores y tener las variables de entorno requeridas

3. **Comenzar de cero**: Para reiniciar en cualquier directorio:
   ```bash
   terraform destroy  # Eliminar recursos
   rm -rf .terraform terraform.tfstate*  # Limpiar archivos locales
   terraform init  # Re-inicializar
   ```

## Asistente de Limpieza

Para limpiar archivos antiguos monolíticos de Terraform (si actualizas desde una versión anterior):

```bash
cd terraform
python cleanup_old_structure.py
```

Esto identificará archivos antiguos que pueden eliminarse de forma segura.