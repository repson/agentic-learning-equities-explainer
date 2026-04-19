# Alex - Guía del Proyecto de Curso "AI in Production"

## Descripción General del Proyecto

**Alex** (Agentic Learning Equities eXplainer) es una plataforma SaaS de planificación financiera empresarial basada en múltiples agentes. Este es el proyecto final para las Semanas 3 y 4 del curso “AI in Production” impartido por Juan Gabriel Gomila en Frogames Formación, que despliega soluciones de Agentes a producción.

El usuario es un estudiante del curso. Estás trabajando con el usuario para ayudarle a construir Alex con éxito. El usuario está trabajando en Cursor (el fork de VS Code) y puede estar en una PC con Windows, Mac (intel o Apple silicon) o una máquina Linux. Todo el código Python se ejecuta con uv y hay proyectos uv en cada directorio que lo necesita. El estudiante está familiarizado con los servicios de AWS (Lambda, App Runner, Cloudfront) y ha sido introducido a Terraform, uv, NextJS y Docker. Tienen alertas de presupuesto configuradas, pero aun así deben revisar regularmente las pantallas de facturación en la consola de AWS para controlar los costos.

El estudiante tiene un usuario root de AWS, y también un usuario IAM llamado "aiengineer" con permisos. Han ejecutado `aws configure` y deben iniciar sesión como el usuario aiengineer con su región predeterminada.

### ¿Qué van a construir los estudiantes?

Los estudiantes desplegarán un sistema completo de IA en producción con:
- **Colaboración multi-agente**: 5 agentes IA especializados trabajando juntos mediante orquestación
- **Arquitectura serverless**: Lambda, Aurora Serverless v2, App Runner, API Gateway, SQS
- **Almacenamiento vectorial optimizado en costo**: S3 Vectors (¡90% más barato que OpenSearch!)
- **Análisis financiero en tiempo real**: Gestión de portafolios, proyecciones de retiro, investigación de mercado
- **Prácticas a nivel producción**: Observabilidad, guardas, seguridad, monitoreo
- **Aplicación full-stack**: Frontend React NextJS con autenticación Clerk

### Objetivos de Aprendizaje

Al completar este proyecto, los estudiantes:
1. Desplegarán y gestionarán infraestructura de IA en producción sobre AWS
2. Implementarán sistemas multi-agente usando el SDK de OpenAI Agents
3. Integrarán AWS Bedrock (con modelo Nova Pro) para capacidades LLM
4. Construirán una búsqueda vectorial rentable con S3 Vectors y embeddings de SageMaker
5. Crear orquestación de agentes serverless con SQS y Lambda
6. Desplegarán una aplicación SaaS full-stack completa
7. Implementarán características empresariales: monitoreo, observabilidad, guardas, seguridad

### Producto Comercial

Alex es un producto SaaS que provee insights sobre portafolios de acciones de los usuarios mediante informes y gráficos. Alex está integrado con Clerk para la gestión de usuarios y la arquitectura de base de datos mantiene los datos de usuarios separados.

---

## Estructura de Directorios

```
alex/
├── guides/              # Guías paso a paso de despliegue (EMPEZAR AQUÍ)
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
│   ├── retirement/      # Agente de proyección de retiro
│   ├── researcher/      # Agente de investigación de mercado (App Runner)
│   ├── ingest/          # Lambda de ingestión de documentos
│   ├── database/        # Librería de base de datos compartida
│   └── api/             # Backend FastAPI para el frontend
│
├── frontend/            # Aplicación React NextJS
│   ├── pages/
│   ├── components/
│   └── lib/
│
├── terraform/           # Infraestructura como código (IMPORTANTE: Directorios independientes)
│   ├── 2_sagemaker/     # Endpoint de embedding SageMaker
│   ├── 3_ingestion/     # S3 Vectors y Lambda de ingestión
│   ├── 4_researcher/    # Servicio de investigación App Runner
│   ├── 5_database/      # Aurora Serverless v2
│   ├── 6_agents/        # Funciones Lambda multi-agente
│   ├── 7_frontend/      # CloudFront, S3, API Gateway
│   └── 8_enterprise/    # Dashboards y monitoreo CloudWatch
│
└── scripts/             # Scripts de despliegue y desarrollo local
    ├── deploy.py        # Despliegue frontend
    ├── run_local.py     # Desarrollo local
    └── destroy.py       # Script de limpieza
```

---

## Estructura del Curso: Las 8 Guías

**IMPORTANTE:** antes de trabajar con el estudiante, DEBES leer todas las guías en la carpeta `guides`, en el orden correcto (1-8), para entender completamente el proyecto.

### Semana 3: Infraestructura de Investigación

**Día 3 - Fundamentos**
- **Guía 1: Permisos AWS** (1_permissions.md)
  - Configura los permisos IAM para el proyecto Alex
  - Crea el grupo AlexAccess con las políticas requeridas
  - Configura AWS CLI y credenciales

- **Guía 2: Despliegue SageMaker** (2_sagemaker.md)
  - Despliega endpoint serverless SageMaker para embeddings
  - Usa el modelo HuggingFace all-MiniLM-L6-v2
  - Prueba la generación del embedding
  - Comprende endpoints serverless vs always-on

**Día 4 - Almacenamiento Vectorial**
- **Guía 3: Pipeline de Ingestión** (3_ingest.md)
  - Crea el bucket S3 Vectors (¡90% de ahorro!)
  - Despliega la función Lambda para ingestión de documentos
  - Configura API Gateway con autenticación por clave API
  - Prueba almacenamiento y búsqueda de documentos

**Día 5 - Agente de Investigación**
- **Guía 4: Agente Investigador** (4_researcher.md)
  - Despliega un agente de investigación autónomo en App Runner
  - Usa AWS Bedrock con modelo Nova Pro
  - Integra servidor Playwright MCP para exploración web
  - Configura un scheduler EventBridge (opcional)
  - **IMPORTANTE**: Actualiza `backend/researcher/server.py` con tu región y modelo

### Semana 4: Plataforma de Gestión de Portafolio

**Día 1 - Base de Datos**
- **Guía 5: Base de Datos e Infraestructura** (5_database.md)
  - Despliega Aurora Serverless v2 PostgreSQL
  - Habilita Data API (¡sin complejidad VPC!)
  - Crea el esquema de la base de datos
  - Carga datos iniciales (22 ETFs)
  - Configura librería de base de datos compartida

**Día 2 - Orquesta de Agentes**
- **Guía 6: Orquesta de Agentes IA** (6_agents.md)
  - Despliega 5 Lambdas agentes (Planner, Tagger, Reporter, Charter, Retirement)
  - Configura la cola SQS para orquestación
  - Configura patrones de colaboración entre agentes
  - Prueba ejecución local y remota
  - Implementa procesamiento paralelo de agentes

**Día 3 - Frontend**
- **Guía 7: Frontend y API** (7_frontend.md)
  - Configura autenticación Clerk
  - Despliega frontend NextJS
  - Crea backend FastAPI en Lambda
  - Configura CDN CloudFront
  - Prueba gestión de portafolio y análisis IA

**Día 4 - Características Empresariales**
- **Guía 8: Nivel Empresarial** (8_enterprise.md)
  - Implementa configuraciones de escalabilidad
  - Añade capas de seguridad (WAF, endpoints VPC, GuardDuty)
  - Configura dashboards y alarmas CloudWatch
  - Implementa guardas y validaciones
  - Añade explicabilidad
  - Configura observabilidad con LangFuse

Como contexto, en semanas previas los estudiantes aprendieron cómo desplegar en AWS, los servicios clave como Lambda y App Runner, y el uso de Clerk para gestión de usuarios (requiere NextJS con Pages Router).

---

## IMPORTANTE: Trabajando con estudiantes - enfoque

Los estudiantes pueden estar en una PC con Windows, Mac (Intel o Apple Silicon) o Linux. Siempre usa uv para TODO el código Python; hay proyectos uv en cada directorio. No hay problema en tener un proyecto uv dentro de otro, aunque uv puede mostrar una advertencia.

Siempre usa `uv add package` y `uv run module.py`, pero NUNCA `pip install xxx`, NUNCA `python -c "code"`, NUNCA `python -m module.py` ni `python script.py`.
Es MUY IMPORTANTE no usar el comando python fuera de un proyecto uv.
Evita los shell scripts o Powershell scripts ya que son dependientes de plataforma. Prefiere fuerte y consistentemente los scripts en Python (vía uv) y la gestión de archivos en el File Explorer de Cursor, ya que esto será claro para todos los estudiantes.

## Trabajando con estudiantes: Principios centrales

### Antes de empezar, siempre lee todas las guías de la carpeta guides para el contexto completo

### 1. **Siempre establecer contexto primero**

Cuando un estudiante pide ayuda:
1. **Pregunta en qué guía/día está** - Es crítico saber qué infraestructura ya está desplegada
2. **Pregunta qué intenta lograr** - Entiende el objetivo antes de meterte al código
3. **Pregunta qué error o comportamiento ve** - Pide el mensaje de error exacto, no la interpretación del estudiante

### 2. **Diagnostica antes de arreglar** ⚠️ MÁS IMPORTANTE

**NO saltes a escribir código antes de entender el verdadero problema.**

Errores comunes a evitar:
- Escribir código defensivo con checks `isinstance()` sin entender la causa raíz
- Añadir bloques try/except que ocultan el error real
- Crear "workarounds" que tapan el problema real
- Hacer varios cambios al mismo tiempo (hace el debugging imposible)

**En vez de eso, sigue este proceso:**
1. **Reproducir el problema** - Pregunta por mensajes de error exactos, logs, comandos usados
2. **Identificar la causa raíz** - Usa logs de CloudWatch, consola AWS, trazas de error
3. **Verifica tu compresión** - Explica lo que piensas que ocurre y confírmalo con el estudiante
4. **Propón el menor cambio posible** - Cambia solo una cosa a la vez
5. **Testea y verifica** - Confirma que el arreglo funciona antes de avanzar

### 3. **Causas raíz comunes (Primero revisa esto)**

Antes de escribir código, verifica estos problemas comunes:

**Docker Desktop no está corriendo** (lo más común con `package_docker.py`)
- El script fallará con una advertencia uv genérica sobre proyectos anidados
- El verdadero problema es que Docker no está corriendo
- Los estudiantes se distraen con la advertencia de uv (esto fue corregido recientemente en el script)
- **Pregunta siempre**: ¿Está Docker Desktop corriendo?

**Problemas de permisos AWS** (lo más común en general)
- Faltan políticas IAM para servicios AWS específicos
- Permisos específicos por región (especialmente perfiles de inferencia en Bedrock)
- Los perfiles de inferencia requieren permisos para MULTIPLES regiones
- **Verifica**: Políticas IAM, configuración de región de AWS, acceso a modelos en Bedrock

**Variables de Terraform no configuradas**
- Cada directorio Terraform necesita su `terraform.tfvars`
- Faltan variables o están incorrectas causando errores difíciles de entender
- **Verifica**: ¿Existe `terraform.tfvars`? ¿Todas las variables requeridas están configuradas?

**Desajustes de región AWS**
- Modelos Bedrock pueden estar disponibles solo en regiones específicas
- Nova Pro requiere perfiles de inferencia
- Acceso entre regiones puede requerir aprobación de modelos Bedrock en varias regiones
- **Verifica**: Consistencia de región en archivos de configuración

**Acceso a modelo no concedido**
- AWS Bedrock necesita solicitudes explícitas de acceso a modelos
- Nova Pro es el modelo recomendado (Claude Sonnet tiene límites estrictos)
- El acceso es por región; los perfiles de inferencia pueden requerir varias regiones
- **Verifica**: consola Bedrock → Acceso a modelos

### 4. **Estrategia de Modelos actual**

**Usa Nova Pro, no Claude Sonnet**
- Nova Pro (`us.amazon.nova-pro-v1:0` o `eu.amazon.nova-pro-v1:0`) es el recomendado
- Requiere perfiles de inferencia para acceso entre regiones
- Claude Sonnet tiene límites demasiado estrictos para este proyecto
- Los estudiantes necesitan solicitar acceso en la consola de Bedrock (posiblemente para varias regiones)

### 5. **Estrategia de pruebas**

Cada directorio de agente tiene dos archivos de test:
- `test_simple.py` - Pruebas locales con mocks (usa `MOCK_LAMBDAS=true`)
- `test_full.py` - Pruebas de despliegue AWS (invocaciones Lambda reales)

Los estudiantes deben:
1. Probar localmente con `test_simple.py`
2. Desplegar con terraform/paquetería
3. Probar el despliegue con `test_full.py`

### 6. **Ayuda a los estudiantes a ayudarse a sí mismos**

Invita a los estudiantes a:
- Leer los errores detenidamente (especialmente en los logs de CloudWatch)
- Revisar en la consola AWS que existan los recursos
- Usar `terraform output` para ver los detalles
- Probar de manera incremental (no desplegar todo de golpe)
- Tener en cuenta los costos de AWS (recuerda destruir cuando no se trabaje activamente)

---

## Estrategia Terraform

### Arquitectura de directorios independientes

Cada directorio terraform (2_sagemaker, 3_ingestion, etc.) es **independiente** y tiene:
- Su propio archivo de estado local (`terraform.tfstate`)
- Su propio archivo de configuración `terraform.tfvars`
- No depende de otros directorios terraform

**Esto es intencional** para fines educativos:
- Los estudiantes pueden desplegar paso a paso, guía por guía
- Los archivos de estado son locales (más simple que remoto/S3)
- Cada parte puede destruirse de manera independiente
- No necesitas bucket de estado ni complejidad adicional
- La infraestructura se puede destruir paso a paso

### Requisitos críticos

**⚠️ Los estudiantes DEBEN configurar `terraform.tfvars` en cada directorio antes de ejecutar terraform apply**

Lo habitual es usar el File Explorer de Cursor para copiar terraform.tfvars.example a terraform.tfvars y modificar los valores en cada directorio.

Si falta o está mal configurado el `terraform.tfvars`:
- Terraform usará valores por defecto (casi siempre incorrectos)
- Los recursos pueden fallar al crearse, con errores difíciles de entender
- Las conexiones entre servicios fallarán

### Gestión de estado Terraform

- Los archivos de estado están `.gitignore`ados automáticamente
- Estado local significa que no necesitas bucket S3
- Los estudiantes pueden ejecutar `terraform destroy` en cada directorio de forma independiente
- Si un estudiante pierde el estado, puede necesitar importar recursos existentes o recrear

## Estrategia de agentes - trasfondo del SDK OpenAI Agents

Cada subdirectorio de Agente tiene una estructura común con patrones idiomáticos.

1. `lambda_handler.py` para la función lambda y ejecución del agente
2. `agent.py` para creación y lógica del Agente
3. `templates.py` para los prompts

Alex usa OpenAI Agents SDK. Asegúrate de usar siempre las APIs más actuales y idiomáticas de OpenAI Agents SDK, reconociendo que el framework es nuevo. Cuando se crea un proyecto nuevo, el package correcto es `openai-agents` y no `agents`. Así que si creas un nuevo proyecto, usa `uv add openai-agents` y luego `from agents import Agent, Runner, trace` en el código.

Alex usa LiteLLM para conectar con Bedrock:

`model = LitellmModel(model=f"bedrock/{model_id}")`

Se usan outputs estructurados y llamada a Tools frecuentemente, pero por una limitación actual en LiteLLM y Bedrock, el mismo Agente no puede usar ambos (outputs estructurados y herramientas) al mismo tiempo. Así que cada implementación de Agente usa una u otra, nunca ambas.

Este es el enfoque idiomático estándar en `lambda_handler`:

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

En los casos en que una Tool necesita saber qué usuario está logueado para hacer la consulta correcta a la base de datos, usamos un enfoque idiomático estándar para pasar contexto a la Tool que funciona muy bien y es recomendado por OpenAI Agents SDK.

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
Y más adelante:
```python
@function_tool
async def get_market_insights(
    wrapper: RunContextWrapper[ReporterContext], symbols: List[str]
) -> str:
...
```

IMPORTANTE: al usar Bedrock mediante LiteLLM, LiteLLM necesita que esta variable de entorno esté definida:  
`os.environ["AWS_REGION_NAME"] = bedrock_region`  
Esto puede ser confuso porque otros servicios a veces esperan `"AWS_REGION"` o `"DEFAULT_AWS_REGION"`. Pero LiteLLM necesita `AWS_REGION_NAME` tal como se documenta aquí: https://docs.litellm.ai/docs/providers/bedrock.


---

## Problemas comunes y solución de errores

Los problemas más comunes se relacionan con la elección de la región AWS. ¡Verifica variables de entorno, settings de terraform (todo debe propagarse desde tfvars)!

### Problema 1: Falla `package_docker.py`

**Síntomas**: El script falla con advertencia uv sobre proyectos anidados y tal vez algún mensaje de error

**Causa raíz (común)**: Docker Desktop no está corriendo o problema de "Docker mounts denied"

**Diagnóstico**:
1. Pregunta: ¿Está Docker Desktop corriendo?
2. Revisa: ¿Pueden correr `docker ps` con éxito?
3. Corrección reciente: Ahora el script da mejores mensajes, pero versiones antiguas eran confusas

**Solución**: Inicia Docker Desktop, espera a que se inicialice por completo y vuelve a intentar

**Si el problema es Mounts Denied**: No puede montar el directorio /tmp como Docker no tiene acceso. Ve a la app de Docker Desktop y añade el directorio mencionado al File Sharing (Configuración -> Recursos -> Compartir archivos), esto lo resolvió para un estudiante.

**NO solución**: Cambiar las configuraciones del proyecto uv (esto es una pista falsa)

### Problema 2: Problemas de región y acceso a modelos Bedrock

**Síntomas**: Errores "Access denied" o "Model not found" al ejecutar agentes

**Causa raíz**: No se concedió acceso al modelo en Bedrock o es la región equivocada

**Diagnóstico**:
1. ¿Qué modelo están intentando usar?
2. ¿En qué región corre el código?
3. ¿Solicitaron acceso al modelo en la consola Bedrock?
4. Para inference profiles: ¿Tienen permisos para varias regiones?
5. ¿Se definen bien las variables de entorno? LiteLLM necesita `AWS_REGION_NAME`. Verifica que nada esté hardcodeado en el código y que tfvars estén correctos. Añade logs para confirmar la región usada.

**Solución**:
1. Ir a la consola Bedrock en la región correcta
2. Haz clic en “Model access”
3. Solicita acceso a Nova Pro
4. Para acceso entre regiones: Configura perfiles de inferencia con permisos multi-región

### Problema 3: Falla Terraform Apply

**Síntomas**: Los recursos no se crean, errores de dependencia, ARN no encontrado

**Causa raíz**: `terraform.tfvars` sin configurar, o valores de guías previas no copiados

**Diagnóstico**:
1. ¿Existe `terraform.tfvars` en este directorio?
2. ¿Todas las variables requeridas están (ver `terraform.tfvars.example`)?
3. En guías posteriores: ¿Tienen los valores output de guías previas?
4. Ejecuta `terraform output` en directorios anteriores para extraer ARNs necesarios

**Solución**:
1. Copia `terraform.tfvars.example` a `terraform.tfvars`
2. Rellena todos los valores requeridos
3. Toma los ARNs de outputs anteriores: `cd terraform/X_previous && terraform output`
4. Actualiza `.env` con los nuevos valores para scripts de Python

### Problema 4: Fallo en funciones Lambda

**Síntomas**: Errores 500, timeouts, “Module not found”

**Causa raíz**: Paquete mal construido, variables de entorno faltantes, permisos IAM

**Diagnóstico**:
1. Revisa los logs en CloudWatch: `aws logs tail /aws/lambda/alex-{agent-name} --follow`
2. Revisa las variables de entorno de la lambda en la consola AWS
3. Verifica que el rol IAM tenga los permisos necesarios
4. ¿El paquete de la Lambda fue construido con Docker para linux/amd64?

**Solución**:
1. Para empaquetado: Ejecuta de nuevo `package_docker.py` con Docker activo
2. Para variables de entorno: Verifícalas en la consola Lambda o `terraform.tfvars`
3. Para permisos: Revisa la política del rol IAM en terraform

### Problema 5: Error en conexión a base de datos Aurora

**Síntomas**: “Cluster not found”, “Secret not found”, errores Data API

**Causa raíz**: Base de datos sin inicializar, ARNs incorrectos, o Data API deshabilitada

**Diagnóstico**:
1. Revisa el estado del cluster: `aws rds describe-db-clusters`
2. Verifica que Data API esté habilitada (debe mostrar `EnableHttpEndpoint: true`)
3. Verifica que los ARNs en las variables de entorno coincidan con los recursos reales
4. La base puede demorar en inicializar (10-15 minutos)

**Solución**:
1. Espera a que el cluster esté en estado “available”
2. Verifica en la consola RDS que Data API esté habilitado
3. Ejecuta `terraform output` en `5_database` para conseguir los ARNs reales
4. Actualiza las variables de entorno con los ARNs correctos

---

## Referencia rápida de arquitectura técnica

### Servicios principales por guía

**Guías 1-2**: Fundamentos
- Permisos IAM
- Endpoint serverless SageMaker (embeddings)

**Guía 3**: Almacenamiento vectorial
- Bucket e índice S3 Vectors
- Función Lambda de ingestión
- API Gateway con clave API

**Guía 4**: Agente de investigación
- Servicio App Runner (Researcher)
- Repositorio ECR
- Scheduler EventBridge (opcional)

**Guía 5**: Base de datos
- Aurora Serverless v2 PostgreSQL
- Data API habilitada
- Secrets Manager para credenciales
- Esquema y datos iniciales – **IMPORTANTE** revisa el esquema

**Guía 6**: Orquesta de Agentes (La importante)
- 5 funciones Lambda: Planner, Tagger, Reporter, Charter, Retirement
- Cada lambda implementada con código simple e idiomático usando OpenAI Agents SDK. Revisa una implementación existente.
- Cola SQS para orquestación
- Bucket S3 para paquetes Lambda (>50MB)
- Permisos IAM inter-servicio

**Guía 7**: Frontend
- Sitio estático NextJS en S3
- CDN CloudFront
- Backend API Gateway + Lambda
- Autenticación Clerk

**Guía 8**: Enterprise
- Dashboards CloudWatch
- Alarmas y monitoreo
- Observabilidad con LangFuse
- Logging avanzado

### Patrón de colaboración entre agentes

```
Solicitud de usuario → SQS Queue → Planner (Orchestrator)
                            ├─→ Tagger (si es necesario)
                            ├─→ Reporter ──┐
                            ├─→ Charter ───┼─→ Resultados → Base de Datos
                            └─→ Retirement ┘
```

### Gestión de costes

**Optimización de costes:**
- Destruye Aurora cuando no trabajes activamente (mayor ahorro)
- Usa `terraform destroy` en cada directorio
- Supervisa costes en AWS Cost Explorer

### Proceso de limpieza

```bash
# Elimina en orden inverso (opcional, pero más limpio)
cd terraform/8_enterprise && terraform destroy
cd terraform/7_frontend && terraform destroy
cd terraform/6_agents && terraform destroy
cd terraform/5_database && terraform destroy  # Máximo ahorro de costes
cd terraform/4_researcher && terraform destroy
cd terraform/3_ingestion && terraform destroy
cd terraform/2_sagemaker && terraform destroy
```

---

## Archivos clave que modifican los estudiantes

### Archivos de configuración
- `.env` - Variables de entorno raíz (agrega valores según avances las guías)
- `frontend/.env.local` - Configuración de Clerk en frontend
- `terraform/*/terraform.tfvars` - Cada dir terraform (copia desde el .example)

### Código que los estudiantes pueden editar
- `backend/researcher/server.py` - Configuración de región y modelo (Guía 4) - Pero esto debería venir de variables y no requerir cambios de código
- plantillas de agentes en `backend/*/templates.py` - Para personalización
- Páginas del frontend para cambios de UI

---

## Cómo obtener ayuda

### Para estudiantes

Si estás atascado:

1. **Revisa cuidadosamente la guía** - Casi todos los pasos tienen sección de troubleshooting
2. **Mira los mensajes de error** - Lee los logs de CloudWatch, no solo el terminal
3. **Verifica prerequisitos** - ¿Está Docker corriendo? ¿Están los permisos listos? ¿Se configuró terraform.tfvars?
4. **Contacta al instructor**:
   - **Publica una pregunta en Frogames Formación** - Incluye número de guía, error exacto y lo que probaste
   - **Email a Juan Gabriel Gomila**: juangabriel@frogames.es

Cuando pidas ayuda, incluye:
- En qué guía/día estás
- Mensaje exacto de error (copia/pega, no expliques con tus palabras)
- Qué comando ejecutaste
- Logs relevantes de CloudWatch si puedes
- Lo que ya intentaste

### Para Claude Code (AI Assistant)

Cuando ayudes a estudiantes:

0. **Prepárate** - Lee todas las guías para estar completamente informado
1. **Establece el contexto** - ¿Qué guía? ¿Cuál es el objetivo?
2. **Pide detalles del error** - Mensajes reales, logs, salida de consola
3. **Diagnostica primero** - No escribas código sin antes entender el problema
4. **Ve un paso a la vez** - Cambios incrementales
5. **Verifica tu entendimiento** - Explica qué crees que pasa antes de arreglar
6. **Mantenlo simple** - Evita soluciones sobre-ingenerizadas

**Recuerda**: Los estudiantes están aprendiendo. El objetivo es ayudarles a entender QUÉ salió mal y cómo arreglarlo, no sólo hacer que desaparezca el error.

---

### Contexto del curso
- Instructor: Juan Gabriel Gomila
- Plataforma: Frogames Formación
- Curso: AI in Production
- Proyecto: "Alex" – Proyecto final semanas 3-4

---

*Esta guía fue creada para ayudar a asistentes IA (como Claude Code) a apoyar eficazmente a estudiantes en el proyecto Alex. Última actualización: octubre 2025*
