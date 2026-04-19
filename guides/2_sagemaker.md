# Construyendo Alex: Parte 2 - Despliegue Serverless en SageMaker

¡Bienvenido de nuevo! En esta guía, desplegaremos un endpoint serverless de SageMaker que generará embeddings para la base de conocimientos de Alex. Esto es un componente crítico: convierte texto en vectores numéricos que se pueden buscar y comparar.

## RECORDATORIO - ¡CONSEJO IMPORTANTE!

Hay un archivo `gameplan.md` en la raíz del proyecto que describe todo el proyecto de Alex para un Agente de IA, para que puedas hacer preguntas y recibir ayuda. También existen los archivos idénticos `CLAUDE.md` y `AGENTS.md`. Si necesitas ayuda, simplemente inicia tu Agente de IA favorito y dale esta instrucción:

> Soy estudiante del curso AI in Production. Estamos en el repositorio del curso. Lee el archivo `gameplan.md` para obtener información sobre el proyecto. Lee este archivo completamente y revisa todas las guías enlazadas cuidadosamente. No inicies ningún trabajo excepto leer y revisar la estructura de directorios. Cuando termines de leer, dime si tienes preguntas antes de empezar.

Después de responder preguntas, indica exactamente en qué guía estás y cualquier problema que encuentres. Ten cuidado de validar cada sugerencia; siempre pregunta por la causa raíz y evidencia de los problemas. Los LLMs suelen sacar conclusiones apresuradas, pero a menudo se corrigen cuando necesitan aportar pruebas.

## Resumen de la Arquitectura

## ¿Por qué SageMaker?

Utilizamos SageMaker por varias razones importantes:
1. **Preparado para producción**: Maneja el escalado, monitoreo y disponibilidad
2. **Rentable**: Los endpoints serverless escalan a cero cuando no están en uso
3. **Habilidad profesional**: SageMaker es ampliamente usado en entornos empresariales de IA

## ¿Qué vamos a construir?

Implementaremos:
- Un modelo de SageMaker que descarga automáticamente `all-MiniLM-L6-v2` desde HuggingFace Hub
- Un endpoint serverless que escala automáticamente
- Infraestructura como Código utilizando Terraform

La belleza de este enfoque: ¡no es necesario preparar el modelo! El contenedor HuggingFace de SageMaker lo gestiona todo.

## Requisitos previos

Antes de empezar:
- Completa [1_permissions.md](1_permissions.md)
- Tener instalado Terraform (versión 1.5+)

## Paso 1: Configura las variables de Terraform

Primero, vamos a preparar la configuración de Terraform para esta guía:

```bash
# Navega al directorio de terraform de SageMaker
cd terraform/2_sagemaker

# Copia el archivo de variables de ejemplo
cp terraform.tfvars.example terraform.tfvars
```

Edita `terraform.tfvars` y configura tu región AWS (debe coincidir con tu DEFAULT_AWS_REGION):
```hcl
aws_region = "us-east-1"  # Usa tu DEFAULT_AWS_REGION de .env
```

## Paso 2: Despliega con Terraform

Ahora vamos a desplegar la infraestructura de SageMaker. ¡Con el enfoque HuggingFace, no es necesario preparar los artefactos del modelo: el modelo se descargará automáticamente desde HuggingFace Hub!

```bash
# Inicializa Terraform (crea el archivo de estado local)
terraform init

# Despliega la infraestructura de SageMaker
terraform apply
```

Cuando se te pida, escribe `yes` para confirmar el despliegue. Esto creará:
- Rol IAM para SageMaker
- Configuración del modelo SageMaker (con el modelo de HuggingFace)
- Endpoint serverless

## Paso 3: Entendiendo lo que se creó

Terraform creó varios recursos:

1. **Rol IAM**: Da a SageMaker los permisos necesarios
2. **Modelo de SageMaker**: Configuración apuntando al modelo de HuggingFace `sentence-transformers/all-MiniLM-L6-v2`
3. **Endpoint Serverless**: El endpoint API para generar embeddings

Después del despliegue, Terraform mostrará salidas importantes incluyendo instrucciones de configuración.

### Guarda tu configuración

**Importante**: Actualiza tu archivo `.env` con el nombre del endpoint:

1. Anota el nombre del endpoint del output de Terraform (debería ser `alex-embedding-endpoint`)
2. Edita `.env` en Cursor
3. Actualiza esta línea:
   ```
   # Part 2 - SageMaker
   SAGEMAKER_ENDPOINT=alex-embedding-endpoint
   ```

💡 **Consejo**: Las salidas de Terraform se muestran al final de `terraform apply`. También puedes verlas en cualquier momento con:
```bash
terraform output
```

## Paso 4: Prueba el Endpoint

Vamos a verificar que el endpoint funciona con una prueba simple:

```bash
# Navega al directorio backend donde está el payload de prueba
cd ../../backend

# Invoca el endpoint y muestra la salida directamente en la consola
aws sagemaker-runtime invoke-endpoint --endpoint-name alex-embedding-endpoint --content-type application/json --body fileb://vectorize_me.json --output json /dev/stdout
```

Verás un array JSON con 384 números de punto flotante; ese es el texto "vectorize me" convertido en embedding vectorial.

**Nota**: La primera petición a un endpoint serverless puede tardar 10-60 segundos (cold start). Las peticiones siguientes serán mucho más rápidas.

## Análisis de Costos

Tu endpoint serverless:
- **Escala a cero**: Sin cargos cuando no está en uso
- **Precio por petición**: ~$0.00002 por segundo de cómputo
- **Memoria**: 3GB asignados (límite por defecto en AWS para serverless)
- **Costo estimado**: $1-2/mes para un uso típico (1000 peticiones/día)

## Resolución de Problemas

Si la invocación del endpoint falla:

1. **Verifica el estado del endpoint**:
```bash
aws sagemaker describe-endpoint --endpoint-name alex-embedding-endpoint
```
El estado debe ser "InService"

2. **Consulta los logs de CloudWatch**:
```bash
aws logs tail /aws/sagemaker/Endpoints/alex-embedding-endpoint --follow
```

3. **Verifica el ID del modelo HuggingFace**:
Comprueba que el endpoint esté configurado con el modelo correcto:
```bash
aws sagemaker describe-model --model-name alex-embedding-model --query 'PrimaryContainer.Environment'
```
Debe mostrar: `{"HF_MODEL_ID": "sentence-transformers/all-MiniLM-L6-v2", "HF_TASK": "feature-extraction"}`

**Nota**: Si no estás en la región por defecto, añade `--region your-region` a estos comandos.

## Entendiendo Serverless vs Siempre Activo

Elegimos serverless porque:
- **Cold start**: 5-10 segundos (aceptable para nuestro caso de uso)
- **Ahorro de costes**: ~$1-2/mes vs $50-100/mes para siempre activo
- **Auto-escalado**: Maneja picos de tráfico automáticamente

Para sistemas en producción con requisitos estrictos de latencia, podrías elegir endpoints siempre activos.

## MLOps en SageMaker

### ¿Qué es MLOps?

MLOps (Machine Learning Operations) es la práctica de aplicar principios DevOps a sistemas de machine learning. SageMaker es la plataforma integral de AWS para MLOps, proporcionando herramientas para todo el ciclo de vida del ML: preparación de datos, entrenamiento de modelos, despliegue, monitoreo y reentrenamiento.

En sistemas ML en producción necesitas gestionar:
- **Versionado de modelos**: Seguir distintas versiones a medida que evolucionan
- **A/B Testing**: Comparar el rendimiento de modelos en producción
- **Monitoreo de modelos**: Detectar cuando los modelos degradan su desempeño
- **Reentrenamiento automático**: Reentrenar modelos cuando su rendimiento baja
- **Registro de modelos**: Repositorio central para modelos aprobados
- **Automatización de pipelines**: Orquestar todo el flujo de trabajo ML

### Model Drift y por qué importa

**Model drift** ocurre cuando el rendimiento del modelo se degrada con el tiempo porque los datos en producción difieren de los datos de entrenamiento. Para nuestro modelo de embeddings, puede ocurrir drift si:
- El lenguaje evoluciona (aparecen nuevos términos financieros)
- Cambia el comportamiento de usuario (diferentes tipos de consultas)
- Cambian condiciones del mercado (nuevos productos de inversión)

SageMaker Model Monitor puede detectar automáticamente el drift:
- Analizando las distribuciones de predicciones en el tiempo
- Comparando entradas actuales con los datos de entrenamiento
- Alertando cuando las propiedades estadísticas cambian significativamente
- Activando pipelines de reentrenamiento automático

### Explora SageMaker en la consola de AWS

Exploremos qué más puede hacer SageMaker. Ve a la consola y revisa estas secciones:

1. **Ir a la consola de SageMaker**:
   ```
   https://console.aws.amazon.com/sagemaker/
   ```

2. **Explora funcionalidades clave de MLOps** (barra lateral izquierda):
   - **Model Registry**: Descubre cómo los equipos gestionan las versiones de modelos
   - **Pipelines**: Ve cómo se automatizan los flujos ML
   - **Model Monitor**: Observa cómo funciona la detección de drift
   - **Experiments**: Rastrea ejecuciones de entrenamiento e hiperparámetros
   - **Feature Store**: Gestión centralizada de features
   - **Ground Truth**: Servicio de etiquetado de datos

3. **Verifica tu endpoint**:
   - Haz clic en "Inference" → "Endpoints"
   - Busca `alex-embedding-endpoint`
   - Haz clic para ver métricas, configuración y opciones de monitoreo
   - Observa la opción "Data capture" para monitoreo

4. **Explora versiones de modelos**:
   - Haz clic en "Inference" → "Models"
   - Observa cómo SageMaker rastrea artefactos y configuraciones de modelos
   - Cada modelo tiene un ARN único para versionado

### SageMaker vs Bedrock: Cuándo usar cada uno

Ya has trabajado con Bedrock, así que aclaramos cuándo usar cada servicio:

| Aspecto | SageMaker | Bedrock |
|---------|-----------|---------|
| **Caso de uso** | Desplegar TUS modelos o modelos fine-tuned | Usar modelos fundacionales pre-entrenados vía API |
| **Fuente del modelo** | Open source, entrenados a medida o fine-tuned | Modelos gestionados por AWS (Claude, Llama, etc.) |
| **Personalización** | Control total de modelo, entrenamiento e infraestructura | Limitado a prompt engineering y RAG |
| **Modelo de coste** | Pagas por infraestructura (horas de cómputo) | Pagas por cada llamada API (tokens) |
| **Complejidad de setup** | Mayor: gestionas endpoints, escalado y monitoreo | Menor: solo llamadas API |
| **Características de MLOps** | Completo: versionado, monitoreo y pipelines | Mínimo: sólo rastreo de uso |
| **Ideal para** | • Modelos a medida<br>• Modelos fine-tuned<br>• Embeddings especializados<br>• Pipelines ML completos | • Tareas generales de lenguaje<br>• Prototipos rápidos<br>• Capacidades AI estándar |
| **Latencia** | Predecible (siempre activo) o variable (serverless) | Generalmente baja y consistente |
| **Escalado** | Tú gestionas (auto-escalado disponible) | Totalmente gestionado por AWS |

### Decisiones en ejemplos reales

**Usa SageMaker cuando:**
- Necesites un modelo de embedding específico (como nuestro all-MiniLM-L6-v2)
- Has fine-tuned un modelo con datos de tu empresa
- Necesitas control total del versionado y despliegue
- Quieres aplicar procesamiento personalizado (pre/post)
- Necesitas monitorear drift de modelo
- Cumplimiento requiere despliegue local o VPC

**Usa Bedrock cuando:**
- Necesitas comprensión general de lenguaje (como nuestros agentes de la Parte 6)
- Quieres prototipar rápidamente sin infraestructura
- La tarea utiliza prompt engineering
- Quieres acceso a modelos fundacionales de vanguardia
- Quieres minimizar la operación continua
- El modelo de precios por tokens se ajusta a tu uso

### Capacidades Avanzadas de SageMaker

Además de lo que hemos desplegado, SageMaker ofrece:

- **SageMaker Studio**: IDE para desarrollo ML
- **Multi-Model Endpoints**: Hospeda varios modelos en un endpoint
- **Model Compilation (Neo)**: Optimiza modelos para hardware específico
- **Edge Deployment**: Despliega modelos a dispositivos IoT
- **Entrenamiento distribuido**: Entrena modelos grandes en varios GPUs
- **Ajuste de hiperparámetros**: Optimización automatizada de parámetros
- **Batch Transform**: Procesamiento offline de grandes datasets
- **Data Wrangler**: Herramienta visual de preparación de datos

### Prueba esto: Revisa métricas del modelo

Mientras tu endpoint está funcionando, revisa sus métricas en CloudWatch:

```bash
# Visualiza métricas de invocación
aws cloudwatch get-metric-statistics --namespace "AWS/SageMaker" --metric-name "Invocations" --dimensions Name=EndpointName,Value=alex-embedding-endpoint --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) --end-time $(date -u +%Y-%m-%dT%H:%M:%S) --period 300 --statistics Sum --region $(aws configure get region)
```

Esto muestra cómo SageMaker rastrea automáticamente el uso del modelo: ¡esencial para MLOps!

## Resolución de Problemas

### Error "Endpoint Already Exists"

Si ves el error "Cannot create already existing endpoint" durante `terraform apply`, significa que el endpoint se creó pero Terraform perdió seguimiento (generalmente porque se interrumpió el proceso). Para solucionarlo:

**Opción 1: Importar el endpoint existente** (recomendado)
```bash
terraform import aws_sagemaker_endpoint.embedding_endpoint alex-embedding-endpoint
terraform apply
```

**Opción 2: Borrar y recrear**
```bash
aws sagemaker delete-endpoint --endpoint-name alex-embedding-endpoint
# Espera a que se complete el borrado (verifica con describe-endpoint)
terraform apply
```

### Terraform Apply tarda mucho

Los endpoints serverless de SageMaker pueden tardar 3-5 minutos en crearse. ¡Ten paciencia y no interrumpas el proceso! Si lo interrumpes, sigue "Error Endpoint Already Exists" arriba.

### Falla la creación del Endpoint por error en rol IAM

Si ves un error sobre IAM role inválido durante `terraform apply`, es debido a un problema conocido por delays de propagación IAM. La configuración de Terraform incluye una solución agregando un delay de 15 segundos antes de crear el endpoint para que el rol IAM se propague completamente.

Si continúas con problemas:
1. Ejecuta `terraform destroy` para limpiar
2. Espera un minuto para la propagación completa de IAM
3. Ejecuta `terraform apply` de nuevo

El mensaje de error puede ser confuso: a menudo indica límites de cuota o delay de propagación en vez de un error real de IAM.

## Eliminación (opcional)

Si necesitas borrar sólo la infraestructura de SageMaker:

```bash
cd terraform/2_sagemaker
terraform destroy
```

⚠️ Esto solo eliminará los recursos de SageMaker de esta guía, ¡no otras partes!

## Siguientes pasos

¡Felicidades! Has desplegado un modelo de ML listo para producción en AWS.

En la próxima guía:
1. Configuraremos S3 Vectors para almacenamiento vectorial rentable (¡90% más barato!)
2. Crearemos una función Lambda para conectar todo
3. Construiremos una API para ingerir conocimiento financiero

Tu endpoint de SageMaker está listo y esperando. ¡Continuemos construyendo Alex! 🎉

Continúa en: [3_ingest.md](3_ingest.md)