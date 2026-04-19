# Alex - Guía del Proyecto de Curso "IA en Producción"

## Resumen del Proyecto

**Alex** (Agentic Learning Equities eXplainer) es una plataforma SaaS de planificación financiera empresarial basada en agentes múltiples. Es el proyecto final de las semanas 3 y 4 del curso "IA en Producción" impartido por Juan Gabriel Gomila en Frogames Formación, que lleva soluciones agent a producción.

El usuario es un estudiante del curso. Tú trabajas con el usuario para ayudarle a construir Alex con éxito. El estudiante utiliza Cursor (el fork de VS Code) y puede estar en un PC con Windows, un Mac (Intel o Apple silicon) o una máquina Linux. Todo el código Python se ejecuta con uv y hay proyectos uv en cada directorio que lo requiere. El alumno está familiarizado con los servicios de AWS (Lambda, App Runner, Cloudfront) y ha sido introducido a Terraform, uv, NextJS y Docker. Tienen alertas de presupuesto configuradas, pero deben revisar frecuentemente las pantallas de facturación en la consola de AWS para vigilar los costes.

El alumno dispone de un usuario root de AWS y también de un usuario IAM llamado "aiengineer" con permisos. Han ejecutado `aws configure` y deben haber iniciado sesión como el usuario aiengineer con su región por defecto.

### Qué Construirán los Estudiantes

Los estudiantes desplegarán un sistema completo de IA en producción que incluye:
- **Colaboración multiagente**: 5 agentes de IA especializados trabajando juntos mediante orquestación
- **Arquitectura serverless**: Lambda, Aurora Serverless v2, App Runner, API Gateway, SQS
- **Almacenamiento vectorial optimizado en costes**: S3 Vectors (¡90% más barato que OpenSearch!)
- **Análisis financiero en tiempo real**: Gestión de portafolio, proyecciones de jubilación, investigación de mercados
- **Prácticas de nivel producción**: Observabilidad, guardarraíles, seguridad, monitorización
- **Aplicación full-stack**: Frontend React NextJS con autenticación Clerk

### Objetivos de Aprendizaje

Al completar este proyecto, los estudiantes:
1. Desplegarán y gestionarán infraestructura de IA en producción sobre AWS
2. Implementarán sistemas multiagente usando OpenAI Agents SDK
3. Integrarán AWS Bedrock (con el modelo Nova Pro) para capacidades LLM
4. Construirán búsqueda vectorial optimizada usando S3 Vectors y embeddings SageMaker
5. Crearán orquestación serverless de agentes con SQS y Lambda
6. Desplegarán una aplicación SaaS full-stack completa
7. Implementarán funcionalidades empresariales: monitorización, observabilidad, guardarraíles, seguridad

### Producto Comercial

Alex es un producto SaaS que proporciona insights sobre carteras de renta variable de usuarios mediante informes y gráficos. Alex está integrado con Clerk para la gestión de usuarios y la arquitectura de la base de datos mantiene los datos de los usuarios separados.

---

## Estructura del Directorio

```
alex/
├── guides/              # Guías paso a paso de despliegue (EMPIEZA AQUÍ)
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
├── backend/             # Código de los agentes y funciones Lambda
│   ├── planner/         # Agente orquestador
│   ├── tagger/          # Agente de clasificación de instrumentos
│   ├── reporter/        # Agente de análisis de cartera
│   ├── charter/         # Agente de visualización
│   ├── retirement/      # Agente de proyección de jubilación
│   ├── researcher/      # Agente de investigación de mercado (App Runner)
│   ├── ingest/          # Lambda de ingestión de documentos
│   ├── database/        # Librería compartida de base de datos
│   └── api/             # Backend FastAPI para el frontend
│
├── frontend/            # Aplicación React NextJS
│   ├── pages/
│   ├── components/
│   └── lib/
│
├── terraform/           # Infraestructura como código (IMPORTANTE: directorios independientes)
│   ├── 2_sagemaker/     # Endpoint embedding SageMaker
│   ├── 3_ingestion/     # S3 Vectors y Lambda de ingestión
│   ├── 4_researcher/    # Servicio App Runner de investigación
│   ├── 5_database/      # Aurora Serverless v2
│   ├── 6_agents/        # Lambdas multiagente
│   ├── 7_frontend/      # CloudFront, S3, API Gateway
│   └── 8_enterprise/    # Dashboards y monitorización CloudWatch
│
└── scripts/             # Scripts de despliegue y desarrollo local
    ├── deploy.py        # Despliegue del frontend
    ├── run_local.py     # Desarrollo local
    └── destroy.py       # Script de limpieza
```

---

## Estructura del Curso: Las 8 Guías

**IMPORTANTE:** antes de trabajar con el estudiante, DEBES leer todas las guías en la carpeta guides, en el orden correcto (1-8), para comprender completamente el proyecto.

### Semana 3: Infraestructura de Investigación

**Día 3 - Fundamentos**
- **Guía 1: Permisos AWS** (1_permissions.md)
  - Configurar permisos IAM para el proyecto Alex
  - Crear grupo AlexAccess con las políticas necesarias
  - Configurar AWS CLI y credenciales

- **Guía 2: Despliegue de SageMaker** (2_sagemaker.md)
  - Desplegar endpoint serverless SageMaker para embeddings
  - Usar modelo HuggingFace all-MiniLM-L6-v2
  - Probar la generación de embeddings
  - Entender serverless vs endpoints siempre activos

**Día 4 - Almacenamiento Vectorial**
- **Guía 3: Pipeline de Ingesta** (3_ingest.md)
  - Crear bucket S3 Vectors (¡90% de ahorro de costes!)
  - Desplegar Lambda de ingestión de documentos
  - Configurar API Gateway con autenticación por API key
  - Probar almacenamiento y búsqueda de documentos

**Día 5 - Agente de Investigación**
- **Guía 4: Agente Investigador** (4_researcher.md)
  - Desplegar el agente autónomo de investigación en App Runner
  - Usar AWS Bedrock con modelo Nova Pro
  - Integrar Playwright MCP server para navegación web
  - Configurar EventBridge scheduler (opcional)
  - **IMPORTANTE**: Actualiza `backend/researcher/server.py` con tu región y modelo

### Semana 4: Plataforma de Gestión de Portafolios

**Día 1 - Base de Datos**
- **Guía 5: Database e Infraestructura** (5_database.md)
  - Desplegar Aurora Serverless v2 PostgreSQL
  - Habilitar Data API (¡sin complejidad de VPC!)
  - Crear esquema de base de datos
  - Cargar datos de ejemplo (22 ETFs)
  - Configurar librería compartida de base de datos

**Día 2 - Orquesta de Agentes**
- **Guía 6: Orquesta de Agentes IA** (6_agents.md)
  - Desplegar 5 lambdas de agentes (Planner, Tagger, Reporter, Charter, Retirement)
  - Configurar cola SQS para orquestación
  - Definir patrones de colaboración entre agentes
  - Probar ejecución local y remota
  - Implementar el procesamiento paralelo de agentes

**Día 3 - Frontend**
- **Guía 7: Frontend y API** (7_frontend.md)
  - Configurar autenticación Clerk
  - Desplegar frontend React NextJS
  - Crear backend FastAPI sobre Lambda
  - Configurar CDN CloudFront
  - Probar gestión de portafolio y análisis IA

**Día 4 - Features Empresariales**
- **Guía 8: Nivel Empresarial** (8_enterprise.md)
  - Implementar configuración de escalabilidad
  - Añadir seguridad (WAF, endpoints VPC, GuardDuty)
  - Configurar dashboards y alarmas en CloudWatch
  - Implementar guardarraíles y validación
  - Añadir explicabilidad
  - Configurar observabilidad con LangFuse

Como contexto, en semanas anteriores los estudiantes aprendieron a desplegar en AWS, los servicios clave como Lambda y App Runner, y a utilizar Clerk para la gestión de usuarios (requiere NextJS con Pages Router).

---

## IMPORTANTE: Cómo Trabajar con Estudiantes

Los estudiantes pueden estar en Windows, Mac (Intel o Apple Silicon) o Linux. Siempre usa uv para TODO el código Python; hay proyectos uv en cada directorio. No hay problema con tener un proyecto uv dentro de otro, aunque uv puede mostrar un warning.

Haz siempre `uv add package` y `uv run module.py`, pero NUNCA `pip install xxx` y NUNCA `python -c "code"` ni `python -m module.py` ni `python script.py`.
Es MUY IMPORTANTE no usar el comando python fuera de un proyecto uv.
Evita los shell scripts o scripts Powershell ya que dependen del sistema. Prioriza escribir scripts en Python (vía uv) y la gestión de archivos en el Cursor File Explorer, ya que esto será claro para todos los estudiantes.

## Principios Básicos al Ayudar a Estudiantes

### Antes de empezar, lee siempre todas las guías de la carpeta guides para tener todo el contexto

### 1. **Siempre Establece el Contexto Primero**

Cuando un estudiante pide ayuda:
1. **Pregunta en qué guía/día está** - Es crítico para saber qué infraestructura tiene desplegada
2. **Pregunta qué intenta lograr** - Antes de ver el código, entiende el objetivo
3. **Pregunta qué error o comportamiento ve** - Pide el error real, no solo la interpretación

### 2. **Diagnostica Antes de Arreglar** ⚠️ LO MÁS IMPORTANTE

**NO saques conclusiones ni escribas mucho código antes de entender el problema.**

Errores comunes:
- Escribir código defensivo con comprobaciones `isinstance()` sin entender el origen real
- Añadir try/except que esconden el error real
- Crear soluciones alternativas que tapan el problema verdadero
- Hacer múltiples cambios a la vez (dificulta el debug)

**En vez de eso, sigue este proceso:**
1. **Reproduce el problema** - Pide errores exactos, logs, comandos
2. **Identifica la raíz** - Usa logs de CloudWatch, consola de AWS, trazas de error
3. **Verifica el entendimiento** - Explica lo que crees que ocurre y confírmalo con el estudiante
4. **Propón la mínima solución** - Cambia UNA cosa cada vez
5. **Prueba y verifica** - Confirma que funciona antes de seguir

### 3. **Causas Comunes (Revisa Esto Primero)**

Antes de escribir código, chequea estos problemas habituales:

**Docker Desktop No Iniciado** (muy común con `package_docker.py`)
- El script falla con advertencia genérica de uv sobre proyectos anidados
- El problema verdadero es que Docker no está iniciado
- El estudiante puede distraerse con el warning uv (esto ya se arregló en el script)
- **Pregunta siempre**: "¿Está Docker Desktop iniciado?"

**Problemas de Permisos AWS** (lo más común)
- Políticas IAM faltantes para servicios específicos de AWS
- Permisos región-específicos (especialmente para perfiles de inferencia Bedrock)
- Los perfiles de inferencia requieren permisos en MÚLTIPLES regiones
- **Revisa**: Políticas IAM, configuración de región AWS, acceso a modelos en Bedrock

**Variables Terraform No Configuradas**
- Cada directorio terraform necesita su propio `terraform.tfvars`
- Variables faltantes o incorrectas generan errores confusos
- **Revisa**: ¿Existe `terraform.tfvars`? ¿Están todas las variables necesarias?

**Desajustes de Región AWS**
- Algunos modelos Bedrock solo existen en regiones específicas
- Nova Pro requiere perfiles de inferencia
- Acceso entre regiones puede requerir modelos aprobados en Bedrock en varias regiones
- **Revisa**: Coherencia de región en los archivos de configuración

**Acceso a Modelo No Concedido**
- AWS Bedrock requiere solicitud explícita de acceso a modelos
- Nova Pro es el modelo recomendado (Claude Sonnet tiene límites de uso estrictos)
- El acceso es por región; los perfiles de inferencia pueden requerir varias regiones
- **Revisa**: consola de Bedrock → Acceso a modelos

### 4. **Estrategia Actual para Modelos**

**Usa Nova Pro, no Claude Sonnet**
- Nova Pro (`us.amazon.nova-pro-v1:0` o `eu.amazon.nova-pro-v1:0`) es el modelo recomendado
- Requiere perfiles de inferencia para acceso entre regiones
- Claude Sonnet tiene límites de uso demasiado estrictos
- Los estudiantes deben solicitar acceso en la consola de Bedrock, y posiblemente para varias regiones

### 5. **Metodología de Pruebas**

Cada directorio de agente tiene dos archivos de test:
- `test_simple.py` - Test local con mocks (usa `MOCK_LAMBDAS=true`)
- `test_full.py` - Test tras despliegue en AWS (invocación real de Lambda)

Los estudiantes deben:
1. Probar primero localmente con `test_simple.py`
2. Desplegar con terraform/paquetizado
3. Probar tras el despliegue con `test_full.py`

### 6. **Ayuda a que los Estudiantes se Autoayuden**

Anima a los estudiantes a:
- Leer atentamente los mensajes de error (sobre todo logs de CloudWatch)
- Revisar la consola de AWS para verificar que los recursos existen
- Usar `terraform output` para ver detalles de recursos
- Probar incrementalmente (no desplegar todo de golpe)
- Vigilar los costes AWS (recuérdales destruir recursos si no los usan activamente)

---

## Estrategia Terraform

### Arquitectura de Directorios Independientes

Cada directorio terraform (2_sagemaker, 3_ingestion, etc.) es **independiente** con:
- Su propio fichero de estado local (`terraform.tfstate`)
- Su propia configuración `terraform.tfvars`
- Sin dependencias entre directorios terraform

**Esto es intencionado** por motivos didácticos:
- Permite desplegar por partes, guía a guía
- Los ficheros de estado son locales (más simple que con S3 remoto)
- Cada parte se puede destruir de forma independiente
- No hay que configurar buckets de estado complejos
- La infraestructura se puede eliminar paso a paso

### Requisitos Críticos

**⚠️ Los estudiantes DEBEN configurar `terraform.tfvars` en cada directorio antes de ejecutar terraform apply**

Es común usar el File Explorer de Cursor para copiar terraform.tfvars.example a terraform.tfvars y luego modificar las variables en cada carpeta.

Si falta o está mal `terraform.tfvars`:
- Terraform usará valores por defecto (a menudo erróneos)
- Los recursos pueden fallar con errores confusos
- Las conexiones entre servicios se romperán

### Gestión del Estado en Terraform

- Los ficheros de estado están `.gitignored` automáticamente
- El estado local evita necesidad de bucket S3
- Se puede hacer `terraform destroy` en cada directorio sin afectar otros
- Si pierden el estado, puede ser necesario importar recursos o recrear

## Estrategia de Agentes - sobre OpenAI Agents SDK

Cada subdirectorio de agente sigue una estructura común y patrones idiomáticos.

1. `lambda_handler.py` para la función lambda y ejecución del agente
2. `agent.py` para la creación y lógica del agente
3. `templates.py` para los prompts

Alex usa OpenAI Agents SDK. Asegúrate de usar siempre las últimas APIs idiomáticas del SDK, recordando que es un framework nuevo. Aunque ya está instalado en los proyectos uv, el nombre correcto del paquete es `openai-agents` y no `agents`. Por tanto, si creas un proyecto nuevo, usa `uv add openai-agents` y este import: `from agents import Agent, Runner, trace`.

Alex utiliza LiteLLM para conectar con Bedrock:

`model = LitellmModel(model=f"bedrock/{model_id}")`

Se usan outputs estructurados y Tool calling, pero por una limitación actual con LiteLLM y Bedrock, el mismo agente no puede usar ambos a la vez. Así que cada agente implementa o bien outputs estructurados o bien utiliza Tools, nunca ambos.

Este es el enfoque estándar usado en lambda_handler:

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

En los casos en que alguna Tool necesita saber el usuario autenticado para hacer la consulta correcta a la base de datos, usamos un enfoque idiomático y estándar para pasar el contexto a la Tool recomendado por OpenAI Agents SDK:

```python

with trace("Reporter Agent"):
        agent = Agent[ReporterContext](  # Especificar tipo de contexto
            name="Report Writer", instructions=REPORTER_INSTRUCTIONS, model=model, tools=tools
        )

        result = await Runner.run(
            agent,
            input=task,
            context=context,  # Pasar el contexto
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

IMPORTANTE: si usas Bedrock a través de LiteLLM, LiteLLM requiere que esta variable de entorno esté configurada:   
`os.environ["AWS_REGION_NAME"] = bedrock_region`  
Esto puede confundir, ya que otros servicios usan `"AWS_REGION"` o `"DEFAULT_AWS_REGION"`. LiteLLM necesita `AWS_REGION_NAME` como está documentado aquí: https://docs.litellm.ai/docs/providers/bedrock.

---

## Problemas Comunes y Solución de Problemas

Lo más común son los problemas con la región AWS: ¡revisa variables de entorno, settings terraform (todo debería venir de tfvars)!

### Problema 1: Falla `package_docker.py`

**Síntomas**: El script falla con advertencia uv sobre proyectos anidados y quizá un error

**Causa común**: Docker Desktop no está iniciado o denegación de montajes de Docker

**Diagnóstico**:
1. Pregunta: "¿Está Docker Desktop en ejecución?"
2. Comprueba: ¿Funciona `docker ps` correctamente?
3. Solución reciente: El script ahora da mejores mensajes de error, las versiones antiguas no

**Solución**: Inicia Docker Desktop, espera a que cargue completamente e inténtalo de nuevo

**Si el error es Mounts Denied**: Falla al montar el directorio /tmp en Docker por permisos. Ir a Docker Desktop, añadir el directorio del error a los paths compartidos (Settings -> Resources -> File Sharing) lo solucionó para un estudiante.

**No es solución**: Cambiar la config uv (esto no es relevante)

### Problema 2: Problemas de Región y Acceso a Modelo Bedrock denegado

**Síntomas**: "Access denied" o "Model not found" al ejecutar agentes

**Causa**: Acceso a modelo no concedido en Bedrock, o región incorrecta

**Diagnóstico**:
1. ¿Qué modelo estás intentando usar?
2. ¿En qué región corre el código?
3. ¿Se solicitó acceso al modelo en consola Bedrock?
4. Para perfiles de inferencia: ¿Permisos en varias regiones?
5. ¿Las variables de entorno están bien? LiteLLM requiere `AWS_REGION_NAME`. Comprueba que no haya valores hardcodeados y que tfvars sean correctos. Añade logs para ver qué región se usa.

**Solución**:
1. Ve a la consola de Bedrock en la región correcta
2. Haz clic en "Acceso a modelos"
3. Solicita acceso a Nova Pro
4. Para multirregión: configura perfiles de inferencia con permisos en varias regiones

### Problema 3: Falla `terraform apply`

**Síntomas**: Recursos no se crean, errores de dependencias, ARN no encontrado

**Causa**: `terraform.tfvars` no está configurado, o faltan valores de guías previas

**Diagnóstico**:
1. ¿Existe `terraform.tfvars` en este directorio?
2. ¿Están todas las variables necesarias? (mira `terraform.tfvars.example`)
3. Para guías avanzadas: ¿Tienes los outputs de guías anteriores?
4. Corre `terraform output` en esos directorios para obtener los ARN

**Solución**:
1. Copia `terraform.tfvars.example` a `terraform.tfvars`
2. Rellena todos los valores requeridos
3. Consigue los ARN con: `cd terraform/X_previous && terraform output`
4. Actualiza el `.env` para scripts Python

### Problema 4: Lambdas Fallidas

**Síntomas**: Errores 500, timeouts, "Module not found"

**Causa**: Paquete mal construido, faltan env vars, IAM incorrecto

**Diagnóstico**:
1. Mira logs en CloudWatch: `aws logs tail /aws/lambda/alex-{agent-name} --follow`
2. Comprueba variables de entorno en consola Lambda
3. ¿El rol IAM tiene los permisos?
4. ¿Se empaquetó Lambda con Docker para linux/amd64?

**Soluciones**:
1. Empaquetado: Re-ejecuta `package_docker.py` con Docker iniciado
2. Env vars: Verifícalas en consola o `terraform.tfvars`
3. IAM: revisa policy en terraform

### Problema 5: Falla conexión a base de datos Aurora

**Síntomas**: "Cluster not found", "Secret not found", errores Data API

**Causa**: Base de datos sin inicializar, ARNs incorrectos o Data API deshabilitado

**Diagnóstico**:
1. Estado del cluster: `aws rds describe-db-clusters`
2. ¿Data API está habilitado? (debe poner `EnableHttpEndpoint: true`)
3. Comprueba los ARN en variables de entorno
4. ¿La base de datos aún está inicializando? (tarda 10-15 min)

**Soluciones**:
1. Espera a ver "available" en el cluster
2. Verifica el Data API en consola RDS
3. Ejecuta `terraform output` en `5_database` para ARN correctos
4. Actualiza env vars con los ARN reales

---

## Resumen Técnico de Arquitectura

### Servicios Principales por Guía

**Guías 1-2**: Fundamentos
- Permisos IAM
- Endpoint SageMaker Serverless (embeddings)

**Guía 3**: Almacenamiento Vectorial
- Bucket S3 Vectors e índice
- Lambda de ingestión
- API Gateway + API key

**Guía 4**: Agente de Investigación
- Servicio App Runner (Researcher)
- Repositorio ECR
- EventBridge scheduler (opcional)

**Guía 5**: Base de Datos
- Aurora Serverless v2 PostgreSQL
- Data API habilitado
- Secrets Manager para credenciales
- Esquema y seed data base de datos - **IMPORTANTE** lee el esquema

**Guía 6**: Orquesta de Agentes (la principal)
- 5 lambdas: Planner, Tagger, Reporter, Charter, Retirement
- Cada lambda usando OpenAI Agents SDK con código simple. Mira implementaciones para detalles.
- SQS para orquestación
- Bucket S3 para paquetes (>50MB)
- Permisos IAM entre servicios

**Guía 7**: Frontend
- Sitio NextJS estático en S3
- CDN CloudFront
- API Gateway + Lambda backend
- Autenticación Clerk

**Guía 8**: Enterprise
- Dashboards CloudWatch
- Alarmas y monitorización
- Observabilidad LangFuse
- Logging avanzado

### Patrón de Colaboración de Agentes

```
Petición Usuario → SQS → Planner (Orquestador)
                             ├─→ Tagger (si es necesario)
                             ├─→ Reporter ──┐
                             ├─→ Charter ───┼─→ Resultados → Base de Datos
                             └─→ Retirement ┘
```

### Gestión de Costes

**Optimización de costes**:
- Destruye Aurora al no trabajar (mayor ahorro)
- Usa `terraform destroy` en cada directorio
- Monitorea costes en Cost Explorer

### Proceso de Limpieza

```bash
# Destruir en orden inverso (opcional, pero más limpio)
cd terraform/8_enterprise && terraform destroy
cd terraform/7_frontend && terraform destroy
cd terraform/6_agents && terraform destroy
cd terraform/5_database && terraform destroy  # Mayor ahorro
cd terraform/4_researcher && terraform destroy
cd terraform/3_ingestion && terraform destroy
cd terraform/2_sagemaker && terraform destroy
```

---

## Archivos Clave que Editan los Estudiantes

### Archivos de Configuración
- `.env` - Variables de entorno raíz (añadir valores según la guía)
- `frontend/.env.local` - Configuración Clerk en el frontend
- `terraform/*/terraform.tfvars` - Cada carpeta terraform (copiar de .example)

### Archivos de Código que Pueden Modificar
- `backend/researcher/server.py` - Configuración de región y modelo (Guía 4) - esto debe venir de variables, no requiere cambio de código normalmente
- Plantillas de agentes en `backend/*/templates.py` - Para personalización
- Páginas frontend para cambios UI

---

## Buscando Ayuda

### Para Estudiantes

Si te atascas:

1. **Repasa bien la guía** - Casi todos los pasos tienen troubleshooting
2. **Revisa los mensajes de error** - Mira los logs CloudWatch, no solo el terminal
3. **Verifica requisitos previos** - ¿Docker está en marcha? ¿Tienes permisos? ¿Está terraform.tfvars configurado?
4. **Contacta con el instructor**:
   - **Pregunta en Frogames Formación** - Incluye la guía/día, mensaje de error y lo que probaste
   - **Email para Juan Gabriel**: juangabriel@frogames.es

Incluye cuando pidas ayuda:
- Guía/día en la que estás
- Mensaje de error exacto (pega y no resumas)
- Qué comando ejecutaste
- Logs CloudWatch relevantes si los tienes
- Qué has probado ya

### Para Claude Code (AI Assistant)

Cuando ayudes a estudiantes:

0. **Prepárate** - Lee todas las guías para estar informado
1. **Establece el contexto** - ¿Guía? ¿Objetivo?
2. **Consigue detalles de error** - Mensajes, logs, consola
3. **Diagnostica primero** - No escribas código sin entender el problema
4. **Piensa incrementalmente** - Un cambio cada vez
5. **Verifica entendimiento** - Explica antes qué crees que pasa antes de cambiar nada
6. **Simplifica** - No sobre-ingenieríes soluciones

**Recuerda**: Los alumnos están aprendiendo. El objetivo es que entiendan qué fue mal y cómo arreglarlo, no solo tapar el error.

---

### Contexto del Curso
- Instructor: Juan Gabriel Gomila
- Plataforma: Frogames Formación
- Curso: IA en Producción
- Proyecto: "Alex" - Capstone de semanas 3-4

---

*Esta guía fue creada para ayudar a asistentes (como Claude Code) a apoyar eficazmente a los estudiantes del proyecto Alex. Última actualización: Octubre 2025*
