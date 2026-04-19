# Alex - Guía del Proyecto del Curso "IA en Producción"

## Descripción General del Proyecto

**Alex** (Agentic Learning Equities eXplainer) es una plataforma de planificación financiera SaaS empresarial basada en agentes múltiples. Este es el proyecto final para las Semanas 3 y 4 del curso "IA en Producción" impartido por Juan Gabriel Gomila en Frogames Formación, en el que se despliegan soluciones de agentes en producción.

El usuario es un estudiante del curso. Estás colaborando con el usuario para ayudarle a construir Alex con éxito. El usuario trabaja en Cursor (el fork de VS Code), y podría estar en un PC con Windows, un Mac (intel o Apple silicon) o una máquina Linux. Todo el código python se ejecuta con uv y hay proyectos uv en cada directorio que lo requiere. El estudiante está familiarizado con servicios de AWS (Lambda, App Runner, Cloudfront) y ha sido introducido a Terraform, uv, NextJS y docker. Tienen alertas de presupuesto configuradas, pero deben revisar periódicamente las pantallas de facturación en la consola de AWS para vigilar los costes.

El estudiante tiene un usuario root de AWS y también un usuario IAM llamado "aiengineer" con permisos. Han ejecutado `aws configure` y deben haber iniciado sesión como "aiengineer" con su región predeterminada.

### ¿Qué construirán los estudiantes?

Los estudiantes desplegarán un sistema de IA completo de producción que incluye:
- **Colaboración multiagente**: 5 agentes de IA especializados trabajando juntos mediante orquestación
- **Arquitectura sin servidor**: Lambda, Aurora Serverless v2, App Runner, API Gateway, SQS
- **Almacenamiento vectorial optimizado en costes**: S3 Vectors (¡90% más barato que OpenSearch!)
- **Análisis financiero en tiempo real**: Gestión de portafolio, proyecciones de jubilación, investigación de mercados
- **Prácticas de grado de producción**: Observabilidad, protecciones, seguridad, monitoreo
- **Aplicación full-stack**: Frontend NextJS React con autenticación Clerk

### Objetivos de Aprendizaje

Al completar este proyecto, los estudiantes:
1. Desplegarán y gestionarán infraestructura de IA de producción en AWS
2. Implementarán sistemas multiagente usando el SDK OpenAI Agents
3. Integrarán AWS Bedrock (con el modelo Nova Pro) para capacidades LLM
4. Construirán búsqueda vectorial coste-efectiva con S3 Vectors y SageMaker embeddings
5. Crearán orquestación sin servidor de agentes con SQS y Lambda
6. Desplegarán una aplicación SaaS full-stack completa
7. Implementarán características empresariales: monitoreo, observabilidad, protecciones, seguridad

### Producto Comercial

Alex es un producto SaaS que provee información sobre los portafolios de acciones de los usuarios mediante reportes y gráficos. Alex está integrado con Clerk para la gestión de usuarios y la arquitectura de la base de datos mantiene los datos de cada usuario separados.

---

## Estructura de Directorios

```
alex/
├── guides/              # Guías de despliegue paso a paso (COMIENZA AQUÍ)
│   ├── 1_permissions.md
│   ├── 2_sagemaker.md
│   ├── 3_ingest.md
│   ├── 4_researcher.md
│   ├── 5_database.md
│   ├── 6_agents.md
│   ├── 7_frontend.md
│   ├── 8_enterprise.md
│   ├── architecture.md
│   └── agent_architecture.md
│
├── backend/             # Código de agentes y funciones Lambda
│   ├── planner/         # Agente orquestador
│   ├── tagger/          # Agente de clasificación de instrumentos
│   ├── reporter/        # Agente de análisis de portafolio
│   ├── charter/         # Agente de visualización
│   ├── retirement/      # Agente de proyección de jubilación
│   ├── researcher/      # Agente de investigación de mercado (App Runner)
│   ├── ingest/          # Lambda de ingestión de documentos
│   ├── database/        # Librería de base de datos compartida
│   └── api/             # Backend FastAPI para el frontend
│
├── frontend/            # Aplicación NextJS React
│   ├── pages/
│   ├── components/
│   └── lib/
│
├── terraform/           # Infraestructura como código (IMPORTANTE: Directorios independientes)
│   ├── 2_sagemaker/     # Endpoint embeddings SageMaker
│   ├── 3_ingestion/     # S3 Vectors y Lambda ingestión
│   ├── 4_researcher/    # Servicio App Runner de investigación
│   ├── 5_database/      # Aurora Serverless v2
│   ├── 6_agents/        # Funciones Lambda multiagente
│   ├── 7_frontend/      # CloudFront, S3, API Gateway
│   └── 8_enterprise/    # Tableros y monitoreo CloudWatch
│
└── scripts/             # Scripts de despliegue y desarrollo local
    ├── deploy.py        # Despliegue frontend
    ├── run_local.py     # Desarrollo local
    └── destroy.py       # Script de limpieza
```

---

## Estructura del Curso: Las 8 Guías

**IMPORTANTE:** antes de trabajar con el estudiante, DEBES leer todas las guías en la carpeta guides, en el orden correcto (1-8), para entender completamente el proyecto.

### Semana 3: Infraestructura de Investigación

**Día 3 - Fundamentos**
- **Guía 1: Permisos AWS** (1_permissions.md)
  - Configura permisos IAM para el proyecto Alex
  - Crea el grupo AlexAccess con las políticas requeridas
  - Configura AWS CLI y credenciales

- **Guía 2: Despliegue SageMaker** (2_sagemaker.md)
  - Despliega endpoint SageMaker Serverless para embeddings
  - Usa el modelo HuggingFace all-MiniLM-L6-v2
  - Prueba la generación de embeddings
  - Entiende endpoints serverless vs always-on

**Día 4 - Almacenamiento Vectorial**
- **Guía 3: Pipeline de Ingestión** (3_ingest.md)
  - Crea bucket S3 Vectors (¡90% de ahorro!)
  - Despliega función Lambda para ingestión de documentos
  - Configura API Gateway con autenticación por API key
  - Prueba almacenamiento y búsqueda de documentos

**Día 5 - Agente Investigador**
- **Guía 4: Agente Investigador** (4_researcher.md)
  - Despliega agente investigador autónomo en App Runner
  - Usa AWS Bedrock con modelo Nova Pro
  - Integra servidor Playwright MCP para navegación web
  - Configura EventBridge scheduler (opcional)
  - **IMPORTANTE**: Actualiza `backend/researcher/server.py` con tu región y modelo

### Semana 4: Plataforma de Gestión de Portafolios

**Día 1 - Base de Datos**
- **Guía 5: Base de Datos e Infraestructura** (5_database.md)
  - Despliega Aurora Serverless v2 PostgreSQL
  - Habilita Data API (¡sin complejidades de VPC!)
  - Crea el esquema de base de datos
  - Carga datos de ejemplo (22 ETFs)
  - Configura la librería de base de datos compartida

**Día 2 - Orquesta de Agentes**
- **Guía 6: Orquestación de Agentes IA** (6_agents.md)
  - Despliega 5 Lambda agents (Planner, Tagger, Reporter, Charter, Retirement)
  - Configura la cola SQS para orquestación
  - Configura patrones de colaboración entre agentes
  - Prueba ejecución local y remota
  - Implementa procesamiento en paralelo de agentes

**Día 3 - Frontend**
- **Guía 7: Frontend y API** (7_frontend.md)
  - Configura autenticación Clerk
  - Despliega frontend NextJS React
  - Crea backend FastAPI en Lambda
  - Configura CDN CloudFront
  - Prueba la gestión de portafolio y análisis IA

**Día 4 - Características Empresariales**
- **Guía 8: Grado Empresarial** (8_enterprise.md)
  - Implementa configuraciones de escalabilidad
  - Añade capas de seguridad (WAF, VPC endpoints, GuardDuty)
  - Configura tableros y alarmas CloudWatch
  - Implementa protecciones y validación
  - Añade características de explicabilidad
  - Configura observabilidad con LangFuse

Por contexto, en semanas previas los estudiantes aprendieron a desplegar en AWS, los principales servicios AWS como Lambda y App Runner, y el uso de Clerk para gestión de usuarios (requiere NextJS con Pages Router).

---

## IMPORTANTE: Cómo trabajar con estudiantes - enfoque

Los estudiantes pueden estar en PC Windows, Mac (Intel o Apple Silicon) o Linux. Siempre utiliza uv para TODO el código python; hay proyectos uv en cada directorio. No hay problema en tener un proyecto uv dentro de otro, aunque uv puede mostrar una advertencia.

Siempre haz `uv add package` y `uv run module.py`, pero NUNCA `pip install xxx` y NUNCA `python -c "code"` ni `python -m module.py` ni `python script.py`.
Es MUY IMPORTANTE no usar el comando python fuera de un proyecto uv.
Evita scripts de shell o Powershell ya que son dependientes de plataforma. Prefiere escribir scripts python (vía uv) y gestionar archivos en el Explorador de Archivos de Cursor, pues así es más claro para todos los estudiantes.

## Trabajo con Estudiantes: Principios Fundamentales

### Antes de empezar, lee siempre todas las guías de la carpeta guides para tener todo el contexto

### 1. **Primero Establece el Contexto**

Cuando un estudiante solicita ayuda:
1. **Pregunta en qué guía/día están** - Esto es crítico para saber qué infraestructura han desplegado
2. **Pregunta qué están tratando de lograr** - Entiende el objetivo antes de entrar en el código
3. **Pregunta qué error o comportamiento ven** - Solicita el mensaje de error real, no una interpretación

### 2. **Diagnostica Antes de Arreglar** ⚠️ LO MÁS IMPORTANTE

**NO saques conclusiones apresuradas ni escribas mucho código antes de entender el problema a fondo.**

Errores comunes a evitar:
- Escribir código defensivo con comprobaciones `isinstance()` sin entender la causa raíz
- Añadir bloques try/except que ocultan el error real
- Crear soluciones que solo enmascaran el problema real
- Hacer múltiples cambios a la vez (complica el debug)

**En su lugar, sigue este proceso:**
1. **Reproduce el problema** - Pide mensajes de error exactos, logs, comandos
2. **Identifica la causa raíz** - Usa logs CloudWatch, la consola AWS, trazas de error
3. **Verifica tu entendimiento** - Explica qué crees que pasa y confirma con el estudiante
4. **Propón el cambio mínimo** - Un cambio cada vez
5. **Prueba y verifica** - Confirma que la solución funciona antes de seguir

### 3. **Causas Raíz Comunes (Revisa Estas Primero)**

Antes de escribir código, revisa estos problemas comunes:

**Docker Desktop no está activo** (Muy común con `package_docker.py`)
- El script fallará con advertencia genérica uv sobre proyectos anidados
- El problema real es que Docker no está corriendo
- Los estudiantes a menudo se distraen con la advertencia de uv (esto fue corregido recientemente en el script)
- **Pregunta siempre**: "¿Está Docker Desktop en ejecución?"

**Problemas de permisos en AWS** (Lo más común en general)
- Políticas IAM faltantes para ciertos servicios de AWS
- Permisos específicos por región (especialmente para perfiles de inferencia en Bedrock)
- Los perfiles de inferencia requieren permisos para MÚLTIPLES regiones
- **Revisa**: Políticas IAM, configuración de región en AWS, acceso a modelos Bedrock

**Variables Terraform no configuradas**
- Cada directorio de terraform necesita su archivo `terraform.tfvars` configurado
- Variables faltantes o incorrectas causan errores crípticos
- **Comprueba**: ¿Existe `terraform.tfvars`? ¿Están todas las variables requeridas?

**Desajustes de región en AWS**
- Los modelos Bedrock pueden estar solo en ciertas regiones
- Nova Pro requiere perfiles de inferencia
- El acceso entre regiones puede necesitar aprobación de modelos en Bedrock en varias regiones
- **Comprueba**: Consistencia de región en archivos de configuración

**Acceso a modelo no concedido**
- AWS Bedrock requiere solicitudes explícitas de acceso a modelos
- Nova Pro es el modelo recomendado (Claude Sonnet tiene límites muy estrictos)
- El acceso es por región; los perfiles de inferencia pueden requerir múltiples regiones aprobadass
- **Comprueba**: Consola Bedrock → Acceso a modelos

### 4. **Estrategia Actual de Modelos**

**Usa Nova Pro, no Claude Sonnet**
- Nova Pro (`us.amazon.nova-pro-v1:0` o `eu.amazon.nova-pro-v1:0`) es el modelo recomendado
- Requiere perfiles de inferencia para acceso entre regiones
- Claude Sonnet tiene límites demasiado estrictos para este proyecto
- Los estudiantes deben solicitar acceso en la consola Bedrock de AWS, quizás en varias regiones

### 5. **Enfoque de Pruebas**

Cada directorio de agentes tiene dos archivos de prueba:
- `test_simple.py` - Test local con mocks (usa `MOCK_LAMBDAS=true`)
- `test_full.py` - Prueba de despliegue AWS (invocaciones Lambda reales)

Los estudiantes deben:
1. Probar primero localmente con `test_simple.py`
2. Desplegar con terraform/packaging
3. Probar el despliegue con `test_full.py`

### 6. **Ayuda para que los estudiantes se ayuden a sí mismos**

Anima a los estudiantes a:
- Leer cuidadosamente los mensajes de error (especialmente logs en CloudWatch)
- Verificar en la consola AWS que existan los recursos
- Usar `terraform output` para ver detalles de recursos desplegados
- Probar incrementalmente (no desplegar todo de golpe)
- Mantener en mente los costes de AWS (recuerda destruir cuando no estén trabajando)

---

## Estrategia Terraform

### Arquitectura de Directorios Independientes

Cada directorio de terraform (2_sagemaker, 3_ingestion, etc.) es **independiente** con:
- Su propio archivo de estado local (`terraform.tfstate`)
- Su propia configuración `terraform.tfvars`
- Sin dependencias entre directorios de terraform

**Esto es intencional** por motivos educativos:
- Los estudiantes pueden desplegar poco a poco, guía por guía
- Los archivos de estado son locales (más simple que usando S3 remoto)
- Cada parte puede destruirse por separado
- No se necesita configurar bucket de estado complejo
- Se puede destruir la infraestructura paso a paso

### Requisitos Críticos

**⚠️ Los estudiantes DEBEN configurar `terraform.tfvars` en cada directorio antes de ejecutar terraform apply**

El patrón típico es usar el Explorador de Archivos de Cursor para copiar terraform.tfvars.example a terraform.tfvars y después modificar las variables en cada directorio.

Si falta o está mal configurado `terraform.tfvars`:
- Terraform usará valores por defecto (a menudo erróneos)
- Los recursos pueden fallar al crearse con errores crípticos
- Las conexiones entre servicios se romperán

### Gestión del Estado Terraform

- Los archivos de estado están automáticamente en `.gitignore`
- El estado local significa que no se necesita bucket S3
- Los estudiantes pueden ejecutar `terraform destroy` en cada directorio independientemente
- Si un estudiante pierde el estado, puede que deba importar recursos existentes o volver a crearlos

## Estrategia de agentes - trasfondo sobre OpenAI Agents SDK

Cada subdirectorio de Agent tiene una estructura común y patrones idiomáticos.

1. `lambda_handler.py` para la función lambda y ejecución del agente
2. `agent.py` para la creación de Agent y su código
3. `templates.py` para prompts

Alex usa el SDK OpenAI Agents. Asegúrate de usar siempre las APIs idiomáticas más recientes de OpenAI Agents SDK, reconociendo que es un framework nuevo. Aunque ya está instalado en todos los proyectos uv, recuerda que el nombre correcto del paquete es `openai-agents` y no `agents`. Así que si alguna vez creas un proyecto nuevo, deberás hacer `uv add openai-agents` seguido de este import en el código `from agents import Agent, Runner, trace`.

Alex utiliza LiteLLM estándar para conectarse a Bedrock:

`model = LitellmModel(model=f"bedrock/{model_id}")`

Frecuentemente se usan salidas estructuradas y Tool calling, pero debido a una limitación de LiteLLM con Bedrock, el mismo Agent no puede usar ambos a la vez. Así, cada implementación de Agent usa salidas estructuradas *O* tools, nunca ambos.

Este es el enfoque idiomático estándar usado en lambda_handler:

```python
    # Crear agente - importado desde agents.py
    model, tools, task = create_agent(job_id, portfolio_data, user_preferences, db)
    
    # Ejecutar agente
    with trace("Retirement Agent"):
        agent = Agent(
            name="Retirement Specialist",
            instructions=RETIREMENT_INSTRUCTIONS,
            model=model,
            tools=tools
        )
        
        result = await Runner.run(
            agent,
            input=task,
            max_turns=20
        )

        response = result.final_output
```

En los casos donde una Tool necesita saber qué usuario está autenticado para hacer la llamada correcta a DB, usamos un enfoque de paso de contexto estándar e idiomático que funciona muy bien y es recomendado por OpenAI Agents SDK.

```python

with trace("Reporter Agent"):
        agent = Agent[ReporterContext](  # Especifica el tipo de contexto
            name="Report Writer", instructions=REPORTER_INSTRUCTIONS, model=model, tools=tools
        )

        result = await Runner.run(
            agent,
            input=task,
            context=context,  # Pasa el contexto
            max_turns=10,
        )

        response = result.final_output

```
Y después:
```python
@function_tool
async def get_market_insights(
    wrapper: RunContextWrapper[ReporterContext], symbols: List[str]
) -> str:
...
```

IMPORTANTE: al utilizar Bedrock mediante LiteLLM, LiteLLM necesita que esta variable de entorno esté establecida:   
`os.environ["AWS_REGION_NAME"] = bedrock_region`  
Esto puede confundir ya que otros servicios esperan `"AWS_REGION"` o `"DEFAULT_AWS_REGION"`. Pero LiteLLM necesita `AWS_REGION_NAME` como se documenta aquí: https://docs.litellm.ai/docs/providers/bedrock.


---

## Problemas Comunes y Resolución de Errores

¡Los problemas más comunes están relacionados con la elección de la región AWS! Revisa variables de entorno, configuración de terraform (todo debe propagarse desde tfvars).

### Problema 1: `package_docker.py` falla

**Síntomas**: El script falla con advertencia uv sobre proyectos anidados y quizá un mensaje de error

**Causa raíz (común)**: Docker Desktop no está ejecutándose o un error de denegación de montaje en Docker

**Diagnóstico**:
1. Pregunta: "¿Está Docker Desktop en ejecución?"
2. Verifica: ¿Pueden ejecutar correctamente `docker ps`?
3. Actualización reciente: El script ahora da mejores errores, pero las versiones antiguas eran confusas

**Solución**: Inicia Docker Desktop, espera a que se inicialice totalmente y vuelve a intentar

**Si el error es de Mounts Denied**: Falla al montar el directorio /tmp en Docker porque no tiene permisos. Ir a la app Docker Desktop y añadir el directorio mencionado al File Sharing (Settings -> Resources -> File Sharing) lo solucionó para un estudiante.

**No es la solución**: Cambiar configuraciones de proyecto uv (es una pista falsa)

### Problema 2: Problemas de región y Acceso Denegado a Modelo Bedrock

**Síntomas**: Errores "Access denied" o "Model not found" al ejecutar agentes

**Causa raíz**: Acceso al modelo no concedido en Bedrock, o región incorrecta

**Diagnóstico**:
1. ¿Qué modelo intentan usar?
2. ¿En qué región corre su código?
3. ¿Han solicitado acceso al modelo en la consola Bedrock?
4. Para perfiles de inferencia: ¿Tienen permisos en varias regiones?
5. ¿Están bien establecidas las variables de entorno? LiteLLM necesita `AWS_REGION_NAME`. Revisa que nada esté hardcodeado en el código, y que los tfvars estén correctos. Añade logs para confirmar la región usada.

**Solución**:
1. Ve a la consola Bedrock en la región correcta
2. Haz click en "Model access"
3. Solicita acceso a Nova Pro
4. Para uso entre regiones: Configura perfiles de inferencia con permisos multi-región

### Problema 3: Falla terraform apply

**Síntomas**: Los recursos fallan al crearse, errores de dependencia, ARN no encontrado

**Causa raíz**: `terraform.tfvars` no configurado o valores de guías previas ausentes

**Diagnóstico**:
1. ¿Existe `terraform.tfvars` en este directorio?
2. ¿Están todas las variables requeridas? (revisa `terraform.tfvars.example`)
3. Para guías siguientes: ¿Tienen los outputs de guías anteriores?
4. Ejecuta `terraform output` en directorios previos para obtener los ARNs necesarios

**Solución**:
1. Copia `terraform.tfvars.example` a `terraform.tfvars`
2. Completa todos los valores requeridos
3. Obtén ARNs de outputs previos: `cd terraform/X_previous && terraform output`
4. Actualiza el archivo `.env` con los valores correctos para scripts python

### Problema 4: Fallos en Lambda

**Síntomas**: Errores 500, timeouts, "Module not found" en Lambda

**Causa raíz**: Paquete no construido correctamente, variables de entorno ausentes o permisos IAM faltantes

**Diagnóstico**:
1. Revisa logs CloudWatch: `aws logs tail /aws/lambda/alex-{agent-name} --follow`
2. Revisa variables de entorno en la consola Lambda
3. Verifica que el rol IAM tenga permisos requeridos
4. ¿El paquete Lambda fue construido con Docker para linux/amd64?

**Solución**:
1. Para el empaquetado: Corre de nuevo `package_docker.py` con Docker corriendo
2. Para las env vars: Verifica en la consola Lambda o `terraform.tfvars`
3. Para permisos: Revisa la política IAM en terraform

### Problema 5: Falla conexión a la base Aurora

**Síntomas**: "Cluster not found", "Secret not found", errores Data API

**Causa raíz**: Base de datos no inicializada, ARNs incorrectos, o Data API no habilitado

**Diagnóstico**:
1. Revisa estado del cluster: `aws rds describe-db-clusters`
2. Verifica que Data API esté habilitado (`EnableHttpEndpoint: true`)
3. Comprueba que los ARNs en las variables de entorno coincidan con los recursos
4. Puede estar en proceso de inicialización (tarda 10-15 minutos)

**Solución**:
1. Espera que el cluster esté en estado "available"
2. Verifica Data API en la consola RDS
3. Ejecuta `terraform output` en `5_database` para obtener ARNs correctos
4. Actualiza las variables de entorno con los ARNs reales

---

## Referencia Rápida de Arquitectura Técnica

### Servicios principales por guía

**Guías 1-2**: Fundamentos
- Permisos IAM
- Endpoint SageMaker Serverless (embeddings)

**Guía 3**: Almacenamiento vectorial
- Bucket S3 Vectors e índice
- Lambda de ingestión
- API Gateway con API key

**Guía 4**: Agente Investigador
- Servicio App Runner (Researcher)
- Repositorio ECR
- EventBridge scheduler (opcional)

**Guía 5**: Base de datos
- Aurora Serverless v2 PostgreSQL
- Data API habilitado
- Secrets Manager para credenciales
- Esquema y datos semilla - **IMPORTANTE** lee el esquema de la BD

**Guía 6**: Orquesta de Agentes (La gran guía)
- 5 funciones Lambda: Planner, Tagger, Reporter, Charter, Retirement
- Cada Lambda implementada usando OpenAI Agents SDK con código simple e idiomático. Revisa una implementación existente para detalles.
- Cola SQS para orquestación
- Bucket S3 para paquetes Lambda (>50MB)
- Permisos IAM cruzados

**Guía 7**: Frontend
- Sitio estático NextJS en S3
- CDN CloudFront
- API Gateway + backend Lambda
- Autenticación Clerk

**Guía 8**: Empresarial
- Tableros CloudWatch
- Alarmas y monitoreo
- Observabilidad LangFuse
- Logging avanzado

### Patrón de Colaboración entre Agentes

```
Petición usuario → Cola SQS → Planner (Orquestador)
                            ├─→ Tagger (si se necesita)
                            ├─→ Reporter ──┐
                            ├─→ Charter ───┼─→ Resultados → BD
                            └─→ Retirement ┘
```

### Gestión de Costos

**Optimización de costes**:
- Destruye Aurora cuando no trabajes activamente (mayor ahorro)
- Usa `terraform destroy` en cada directorio
- Monitorea costes en AWS Cost Explorer

### Proceso de limpieza

```bash
# Destruye en orden inverso (opcional, pero más limpio)
cd terraform/8_enterprise && terraform destroy
cd terraform/7_frontend && terraform destroy
cd terraform/6_agents && terraform destroy
cd terraform/5_database && terraform destroy  # Gran ahorro de costes
cd terraform/4_researcher && terraform destroy
cd terraform/3_ingestion && terraform destroy
cd terraform/2_sagemaker && terraform destroy
```

---

## Archivos Clave que Modifican los Estudiantes

### Archivos de Configuración
- `.env` - Variables de entorno raíz (ve añadiendo valores según cada guía)
- `frontend/.env.local` - Configuración Clerk del frontend
- `terraform/*/terraform.tfvars` - Cada directorio terraform (copiar desde .example)

### Código que los estudiantes pueden necesitar modificar
- `backend/researcher/server.py` - Configuración de región y modelo (Guía 4) - pero esto debería venir de variables y no requerir cambios de código
- Plantillas de agentes en `backend/*/templates.py` - Para personalización
- Páginas del frontend para modificaciones en la UI

---

## Obtener Ayuda

### Para Estudiantes

Si te atascaste:

1. **Revisa la guía cuidadosamente** - La mayoría de pasos tienen una sección de troubleshooting
2. **Lee los mensajes de error** - Mira los logs en CloudWatch, no solo la terminal
3. **Verifica requisitos previos** - ¿Docker está corriendo? ¿Están los permisos configurados? ¿Se configuró terraform.tfvars?
4. **Contacta al instructor**:
   - **Haz una pregunta en Frogames** - Incluye el número de guía, mensaje de error y qué intentaste
   - **Email Juan Gabriel**: juangabriel@frogames.es

Cuando pidas ayuda, incluye:
- ¿En qué guía/día estás?
- Mensaje exacto de error (copia/pega, no lo resumas)
- Qué comando ejecutaste
- Logs CloudWatch relevantes si tienes
- Qué has intentado hasta ahora

### Para Claude Code (Asistente de IA)

Al ayudar a estudiantes:

0. **Prepárate** - Lee todas las guías para ponerte en contexto.
1. **Establece el contexto** - ¿Qué guía? ¿Cuál es el objetivo?
2. **Obtén detalles del error** - Mensajes reales, logs, consola
3. **Diagnostica primero** - No escribas código sin entender el problema
4. **Piensa incrementalmente** - Un cambio cada vez
5. **Verifica tu comprensión** - Explica qué crees que ocurre antes de arreglar
6. **Hazlo simple** - Evita sobreingeniería

**Recuerda**: Los estudiantes están aprendiendo. El objetivo es ayudarles a entender qué ocurrió y cómo arreglarlo, no solo eliminar el error.

---

### Contexto del Curso
- Instructor: Juan Gabriel Gomila
- Plataforma: Frogames Formación
- Curso: IA en Producción
- Proyecto: "Alex" - Proyecto final Semanas 3-4

---

*Esta guía fue creada para ayudar a asistentes de IA (como Claude Code) a apoyar efectivamente a estudiantes con el proyecto Alex. Última actualización: octubre de 2025*
