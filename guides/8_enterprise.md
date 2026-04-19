# Guía 8: Nivel Empresarial - Escalabilidad, Seguridad, Monitoreo, Guardrails y Observabilidad

¡Bienvenido a la guía final de la serie de despliegue de Alex Financial Advisor! En esta guía, transformaremos nuestra aplicación en un sistema listo para producción y apto para empresas implementando buenas prácticas para la escalabilidad, seguridad, monitoreo, guardrails, explicabilidad y observabilidad.

Al finalizar esta guía, tu Alex Financial Advisor será:

- **Escalable**: Listo para manejar tráfico de nivel empresarial
- **Seguro**: Protegido con múltiples capas de seguridad
- **Monitorizado**: Visibilidad total en la salud y rendimiento del sistema
- **Protegido**: Resguardado contra alucinaciones de IA y errores
- **Explicable**: La toma de decisiones de la IA es transparente
- **Observable**: Trazabilidad completa de todas las interacciones de los agentes

## RECORDATORIO - ¡CONSEJO IMPORTANTE!

Hay un archivo `gameplan.md` en la raíz del proyecto que describe todo el proyecto Alex para un Agente de IA, para que puedas hacer preguntas y obtener ayuda. También hay un archivo idéntico `CLAUDE.md` y `AGENTS.md`. Si necesitas ayuda, simplemente inicia tu Agente de IA favorito y dale esta instrucción:

> Soy un estudiante del curso AI in Production. Estamos en el repositorio del curso. Lee el archivo `gameplan.md` para obtener información general del proyecto. Lee este archivo completamente y lee todas las guías enlazadas cuidadosamente. No comiences ningún trabajo aparte de leer y revisar la estructura de directorios. Cuando termines toda la lectura, hazme saber si tienes preguntas antes de que empecemos.

Después de responder las preguntas, indica exactamente en qué guía te encuentras y cualquier problema. Ten cuidado al validar cada sugerencia; siempre pregunta por la causa raíz y evidencia de los problemas. Los LLM tienden a sacar conclusiones precipitadas, pero a menudo se corrigen cuando deben aportar evidencia.

## Sección 1: Escalabilidad

Nuestra arquitectura serverless ya está diseñada para escalado automático, pero vamos a explorar cómo configurarla para tráfico a nivel empresarial.

### Entendiendo la Escalabilidad Serverless

La ventaja de nuestra arquitectura serverless es que AWS escala los componentes automáticamente según la demanda:

1. **Funciones Lambda** escalan automáticamente:

   - Ejecuciones concurrentes: Por defecto 1,000 (se puede aumentar a 10,000+)
   - Cada agente puede manejar múltiples solicitudes simultáneamente
   - No se requiere gestión de servidores

2. **Aurora Serverless v2** escala automáticamente:

   - De 0.5 a 1 ACU (Aurora Capacity Units) por defecto
   - Puede escalar hasta 128 ACUs para tráfico alto
   - Escala en ~15 segundos de acuerdo a la carga

3. **API Gateway** maneja millones de solicitudes:

   - Límite por defecto: 10,000 solicitudes/segundo
   - Ráfaga: 5,000 solicitudes
   - Se puede aumentar a través de soporte de AWS

4. **SQS** ofrece rendimiento ilimitado:
   - Colas estándar: Casi ilimitadas TPS
   - Colas FIFO: 300 mensajes/segundo (se puede agrupar hasta 3,000)

### Configuración para Mayor Escalabilidad

Para prepararte para tráfico empresarial, puedes ajustar estos parámetros en las configuraciones de Terraform:

**En `terraform/5_database/main.tf`:**

```hcl
resource "aws_rds_cluster" "aurora" {
  # Incrementar la capacidad máxima para tráfico alto
  serverlessv2_scaling_configuration {
    max_capacity = 16  # Incrementar de 1 a 16 ACUs
    min_capacity = 0.5 # Mantener el mínimo bajo para eficiencia en costos
  }
}
```

**En `terraform/6_agents/main.tf`:**

```hcl
resource "aws_lambda_function" "planner" {
  # Incrementar la memoria para procesar más rápido
  memory_size = 10240  # Incrementar de 3072 a 10GB
  timeout     = 900    # Mantener máx. en 15 minutos

  # Añadir ejecuciones concurrentes reservadas para capacidad garantizada
  reserved_concurrent_executions = 100  # Garantizar 100 concurrentes
}
```

**En `terraform/7_frontend/main.tf`:**

```hcl
resource "aws_apigatewayv2_stage" "api" {
  # Configurar limitaciones por protección
  default_route_settings {
    throttle_rate_limit  = 10000  # Solicitudes por segundo
    throttle_burst_limit = 5000   # Capacidad de ráfaga
  }
}
```

### Pruebas de Carga de Tu Aplicación

Antes de ir a producción, prueba tu escalabilidad:

**Para macOS/Linux:**

```bash
# Instalar Apache Bench
apt-get install apache2-utils  # Ubuntu/Debian
brew install apache2-utils     # macOS

# Probar el endpoint de la API (sustituye con tu URL de API)
ab -n 1000 -c 50 -H "Authorization: Bearer YOUR_TOKEN" \
   https://your-api.execute-api.region.amazonaws.com/api/user
```

**Para Windows:**

```powershell
# Instalar Apache Bench vía XAMPP o usar Invoke-WebRequest de PowerShell
# Opción 1: Descargar XAMPP que incluye Apache Bench
# Visitar: https://www.apachefriends.org/download.html

# Opción 2: Usar PowerShell para prueba de carga simple
$headers = @{"Authorization" = "Bearer YOUR_TOKEN"}
$url = "https://your-api.execute-api.region.amazonaws.com/api/user"

# Ejecutar 100 solicitudes secuenciales
1..100 | ForEach-Object {
    Invoke-WebRequest -Uri $url -Headers $headers -Method GET
    Write-Host "Request $_ completed"
}

# Para solicitudes concurrentes, considera usar una herramienta como JMeter (multiplataforma)
# Descárgalo de: https://jmeter.apache.org/download_jmeter.cgi
```

### Optimización de Costos a Escala

Monitorea y optimiza los costos mientras escalas:

1. **Usa AWS Cost Explorer** para rastrear tu gasto
2. **Configura alertas de facturación** para costos inesperados
3. **Optimiza el caché de CloudFront** - Aunque CloudFront almacena en caché automáticamente contenido estático de tu bucket de S3, puedes mejorar el rendimiento y reducir costos ajustando comportamientos de caché. Establece TTL más largos para recursos que cambian poco (imágenes, CSS, JS) usando encabezados Cache-Control. Esto reduce las solicitudes al origen (S3), bajando los costos de transferencia y mejorando los tiempos de respuesta.
4. **Considera Step Functions** para orquestaciones complejas a escala

## Sección 2: Seguridad

Nuestra aplicación ya implementa diversas buenas prácticas de seguridad. Vamos a repasarlas y explorar funcionalidades de seguridad empresarial adicionales.

### Implementación Actual de Seguridad

#### 1. **IAM Acceso de Menor Privilegio**

Cada función Lambda tiene los permisos mínimos requeridos:

```hcl
# En terraform/6_agents/main.tf
resource "aws_iam_role_policy" "planner_policy" {
  policy = jsonencode({
    Statement = [
      {
        Effect = "Allow"
        Action = ["rds-data:ExecuteStatement", "rds-data:BatchExecuteStatement"]
        Resource = "arn:aws:rds-db:*:*:cluster:alex-database"
      },
      {
        Effect = "Allow"
        Action = ["lambda:InvokeFunction"]
        Resource = [
          "arn:aws:lambda:*:*:function:alex-tagger",
          "arn:aws:lambda:*:*:function:alex-reporter",
          "arn:aws:lambda:*:*:function:alex-charter",
          "arn:aws:lambda:*:*:function:alex-retirement"
        ]
      }
    ]
  })
}
```

#### 2. **Autenticación JWT con Clerk**

Todas las llamadas a la API requieren tokens JWT válidos:

- Los tokens expiran después de 1 hora
- **Endpoint JWKS para rotación de claves** - Clerk rota automáticamente las claves de firma por seguridad. El endpoint JWKS (JSON Web Key Set) provee las claves públicas actuales usadas para verificar firmas JWT. Así, en caso de compromiso de clave, se rota automáticamente y tu app obtiene las nuevas sin cambios de código.
- **Contexto de usuario validado en cada petición** - Cada llamada incluye un token JWT verificado criptográficamente usando las claves públicas de Clerk. Esto asegura que el usuario es quien dice ser, su sesión sigue válida y el token no fue manipulado. Tokens inválidos o expirados se rechazan antes de cualquier lógica de negocio.

#### 3. **Limitación de API Gateway**

**Protección contra DDoS y abuso** - Los ataques DDoS (Denegación de Servicio Distribuido) intentan saturar tu aplicación inundándola de solicitudes múltiples. El throttling de API Gateway limita solicitudes por segundo, rechazando el exceso automáticamente. Así proteges tus Lambdas y evitas costos descontrolados originados por tráfico malicioso:

```hcl
throttle_rate_limit  = 100   # 100 solicitudes por segundo por usuario
throttle_burst_limit = 200   # Capacidad de ráfaga
```

#### 4. **Control de CORS**

Configuración CORS estricta:

- **Validación de origen** - Solo permite solicitudes desde tu dominio frontend específico, evitando que sitios maliciosos hagan llamadas en nombre del usuario
- **No se permiten credenciales con orígenes comodín** - Previene robo de credenciales asegurando que cookies/tokens de autenticación solo se envíen a orígenes explícitamente confiables
- **Caché preflight para rendimiento** - El navegador guarda las respuestas preflight, reduciendo las peticiones OPTIONS y mejorando la respuesta API

#### 5. **Protección XSS**

**Prevención de Cross-Site Scripting (XSS)** - Los ataques XSS inyectan scripts maliciosos en tus páginas ejecutándose en el navegador del usuario, robando credenciales o datos personales. Las cabeceras Content Security Policy (CSP) indican al navegador qué orígenes de contenido son válidos, bloqueando scripts no autorizados:

```javascript
// En las páginas frontend
<meta
  httpEquiv="Content-Security-Policy"
  content="default-src 'self'; script-src 'self' 'unsafe-inline' https://clerk.com; style-src 'self' 'unsafe-inline';"
/>
```

#### 6. **Gestión de Secretos**

Usando AWS Secrets Manager:

- Credenciales de base de datos nunca en el código
- Rotación automática disponible
- Cifrado en reposo con KMS

**Para ver tus secretos:** Ve a AWS Console → Secrets Manager → Selecciona tu región (us-east-1) → Verás secretos como `alex-database-secret` con las credenciales Aurora

### Características Extra de Seguridad Empresarial

Para robustecer aún más la seguridad, considera implementar:

#### 1. **AWS WAF (Web Application Firewall)**

**AWS WAF** añade otra capa de protección filtrando tráfico web malicioso antes de llegar a tu aplicación. Protege contra ataques conocidos como SQL Injection, XSS y bots. WAF utiliza reglas para inspeccionar cada solicitud y puede bloquear, permitir o contar solicitudes según condiciones definidas. Es un servicio adicional de pago, según reglas y número de solicitudes.

Añadir en `terraform/7_frontend/main.tf`:

```hcl
resource "aws_wafv2_web_acl" "api_protection" {
  name  = "alex-api-waf"
  scope = "REGIONAL"

  default_action {
    allow {}
  }

  rule {
    name     = "RateLimitRule"
    priority = 1

    statement {
      rate_based_statement {
        limit              = 2000
        aggregate_key_type = "IP"
      }
    }

    action {
      block {}
    }
  }

  rule {
    name     = "SQLiRule"
    priority = 2

    statement {
      managed_rule_group_statement {
        vendor_name = "AWS"
        name        = "AWSManagedRulesSQLiRuleSet"
      }
    }

    override_action {
      none {}
    }
  }
}
```

#### 2. **VPC Endpoints para Comunicación Privada**

**VPC Endpoints** permiten que tus Lambdas se comuniquen con AWS sin que el tráfico salga a internet pública. Así mejoras la seguridad, reduces costos de transferencia de datos y obtienes menor latencia. Los endpoints VPC son gratuitos de crear, se cobra el procesamiento de datos (~$0.01/GB). Es ideal en entornos de máxima seguridad donde los datos nunca deben salir de AWS.

Mantener el tráfico dentro de AWS:

```hcl
resource "aws_vpc_endpoint" "s3" {
  vpc_id       = aws_vpc.main.id
  service_name = "com.amazonaws.region.s3"
}
```

#### 3. **AWS GuardDuty para Detección de Amenazas**

**AWS GuardDuty** es un servicio gestionado de detección de amenazas que monitorea cuentas y cargas de trabajo por actividad maliciosa. Utiliza machine learning sobre VPC Flow Logs, eventos CloudTrail y logs DNS para detectar minería de criptomonedas, robo de credenciales, llamadas API atípicas, etc. No requiere infraestructura, pero es de pago (~$1 por GB de logs analizados). Es muy útil para detectar ataques sofisticados que podrían evadir otras capas.

```hcl
resource "aws_guardduty_detector" "main" {
  enable = true
  finding_publishing_frequency = "FIFTEEN_MINUTES"
}
```

#### 4. **Validación de Parámetros**

Añadir en Lambdas:

```python
from pydantic import validator
import re

class PositionCreate(BaseModel):
    symbol: str

    @validator('symbol')
    def validate_symbol(cls, v):
        if not re.match(r'^[A-Z]{1,5}$', v):
            raise ValueError('Invalid symbol format')
        return v
```

## Sección 3: Monitoreo

Vamos a mejorar nuestros logs y crear dashboards de CloudWatch para monitorear la app.

### Implementación Mejorada de Logs

Primero, aseguremos que agentes y API tengan logs completos:

**Para la API (`backend/api/main.py`):**

```python
import logging
import json
from datetime import datetime

# Configura logs estructurados
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class StructuredLogger:
    @staticmethod
    def log_event(event_type, user_id=None, details=None):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "details": details
        }
        logger.info(json.dumps(log_entry))

# Añadir al endpoint
@app.post("/api/analyze")
async def trigger_analysis(user=Depends(clerk_guard)):
    StructuredLogger.log_event(
        "ANALYSIS_TRIGGERED",
        user_id=user.clerk_user_id,
        details={"accounts": user_id}
    )
    # ... resto del endpoint
```

**Para agentes (ejemplo en `backend/planner/lambda_handler.py`):**

```python
import logging
import json
from datetime import datetime, timezone

logger = logging.getLogger()
logger.setLevel(logging.INFO)

async def run_orchestrator(job_id: str) -> None:
    start_time = datetime.now(timezone.utc)

    # Obtener el job para loggear quién hizo la solicitud
    job = db.jobs.find_by_id(job_id)
    if not job:
        logger.error(f"Planner: Job {job_id} not found.")
        return
    user_id = job["clerk_user_id"]

    logger.info(json.dumps({
        "event": "PLANNER_STARTED",
        "job_id": job_id,
        "user_id": user_id,
        "timestamp": start_time.isoformat(),
    }))

    # ... realizar tagging, actualización de precios, etc. ...

    for agent_name in ["reporter", "charter", "retirement"]:
        logger.info(json.dumps({
            "event": "AGENT_INVOKED",
            "agent": agent_name,
            "job_id": job_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }))

    # ... correr el agente planner con Runner.run(...) ...

    end_time = datetime.now(timezone.utc)
    logger.info(json.dumps({
        "event": "PLANNER_COMPLETED",
        "job_id": job_id,
        "duration_seconds": (end_time - start_time).total_seconds(),
        "status": "success",
        "timestamp": end_time.isoformat(),
    }))
```

### Despliegue y Verificación de Cambios de Log

Tras agregar logging estructurado (ya lo tienes en `backend/planner/lambda_handler.py`), debes desplegar y verificar:

1.  **Empaqueta el nuevo código:**

```bash
# Ir al directorio backend
cd backend

# Ejecutar el script de empaquetado
uv run package_docker.py
```

2.  **Despliega el paquete a AWS:**

```bash
# Desde backend
uv run deploy_all_lambdas.py
```

3.  **Lanza un nuevo análisis:** Ingresa en tu sitio en CloudFront y prueba un nuevo análisis de portafolio, luego revisa los logs en CloudWatch.

### Crear Dashboards en CloudWatch

Desde el directorio terraform, desde 8_enterprise:

Copia terraform.tfvars.example a terraform.tfvars y actualiza los valores como siempre.

Después:

`terraform init`

`terraform apply`

Y sigue instrucciones para levantar tus nuevos dashboards de CloudWatch para Bedrock, SageMaker y actividad de los agentes.

#### 3. **Monitoreo de Queues SQS**

En la consola SQS visualiza:

- Mensajes en vuelo
- Edad de los mensajes
- Métricas de throughput
- **Monitoreo DLQ (Dead Letter Queue)** - Mensajes fallidos pasan automáticamente al DLQ tras varios intentos. Monitorea el DLQ para detectar patrones de fallos. Configura alarmas CloudWatch cuando aparezcan mensajes para investigar rápido.

### Configuración de Alarmas CloudWatch

Para crear alarmas de métricas críticas, usa la AWS Console:

1. **Inicia sesión en AWS Console** como root (o usuario IAM con permisos de CloudWatch)
2. **Ve a CloudWatch** → Click en "Alarms" en el menú lateral → "Create alarm"
3. **Selecciona métrica** → "Lambda" → "By Function Name" → Elige tu función (ej: alex-api)
4. **Configura la alarma:**
   - Métrica: Errors
   - Estadística: Sum
   - Período: 5 minutos
   - Umbral: Mayor que 5
5. **Configura notificación** → Nuevo SNS topic → Ingresa email → Confirma por email
6. **Pon nombre a la alarma** (ej: "alex-api-errors") y créala

Repite para otras métricas críticas como Duración, Throttles y Ejecuciones Concurrentes.

### Monitoreo de Costos

**¡Ya tienes alertas de billing desde guías previas!** Recuerda revisar tus gastos regularmente:

1. **AWS Console** → Dashboard de Facturación (menú superior derecho)
2. **Revisa los cargos del mes** - Ve a "Bills"
3. **Monitorea tus alertas de presupuesto** - Debes tener alertas al 50%, 80% y 100%
4. **Usa Cost Explorer** para análisis detallado - Filtra por servicio para saber qué consume más

**¡Revisa costos frecuentemente!** Durante desarrollo y tras cualquier despliegue; Lambda y API Gateway pueden salir costosos con mucho tráfico.

## Sección 4: Guardrails

**Los guardrails son mecanismos de seguridad esenciales en sistemas IA.** Aunque los frameworks avanzados suelen incluir guardrails sofisticados, en esencia, los guardrails son validaciones que implementas en tu código: pruebas que ejecutas antes o después del agente para asegurar que las salidas sean seguras y correctas. Los mejores guardrails están en el código, donde tienes control absoluto sobre la lógica.

Impletemos validaciones y chequeos para evitar que errores de IA afecten a los usuarios.

### Validación de Salida del Charter Agent

Agrega este código de validación en `backend/charter/agent.py` para asegurar que la salida sea JSON bien formado:

```python
import json
import logging
from typing import Dict, Any

logger = logging.getLogger()

def validate_chart_data(chart_json: str) -> tuple[bool, str, Dict[Any, Any]]:
    """
    Valida que la salida del charter agent sea JSON bien formado con la estructura esperada.
    Retorna (is_valid, error_message, parsed_data)
    """
    try:
        # Parsear JSON
        data = json.loads(chart_json)

        # Validar estructura esperada
        required_keys = ["charts"]
        if not all(key in data for key in required_keys):
            return False, f"Missing required keys. Expected: {required_keys}", {}

        # Validar que charts sea arreglo
        if not isinstance(data["charts"], list):
            return False, "Charts must be an array", {}

        # Validar cada gráfico
        for i, chart in enumerate(data["charts"]):
            if "type" not in chart:
                return False, f"Chart {i} missing 'type' field", {}

            if "data" not in chart:
                return False, f"Chart {i} missing 'data' field", {}

            # Validar que data es array
            if not isinstance(chart["data"], list):
                return False, f"Chart {i} data must be an array", {}

            # Verificar campos según tipo de gráfico
            if chart["type"] == "pie":
                for point in chart["data"]:
                    if "name" not in point or "value" not in point:
                        return False, f"Pie chart data points must have 'name' and 'value'", {}
            elif chart["type"] == "bar":
                for point in chart["data"]:
                    if "category" not in point:
                        return False, f"Bar chart data points must have 'category'", {}

        return True, "", data

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON from charter agent: {e}")
        return False, f"Invalid JSON: {e}", {}
    except Exception as e:
        logger.error(f"Unexpected error validating chart data: {e}")
        return False, f"Validation error: {e}", {}

# Usar en tu charter agent:
async def run_charter_agent(job_id: str, task: str) -> str:
    # ... código existente del agente ...

    result = await Runner.run(agent, input=task, max_turns=10)

    # Validar salida
    is_valid, error_msg, parsed_data = validate_chart_data(result.final_output)

    if not is_valid:
        logger.error(f"Charter agent produced invalid output for job {job_id}: {error_msg}")
        # Retorno seguro
        return json.dumps({
            "charts": [],
            "error": "Unable to generate charts at this time"
        })

    return json.dumps(parsed_data)
```

### Guardrails de Validación de Entrada

Agrega a todos los agentes para evitar prompt injection:

```python
def sanitize_user_input(text: str) -> str:
    """Remover intentos potenciales de prompt injection"""
    # Eliminar patrones comunes de inyección
    dangerous_patterns = [
        "ignore previous instructions",
        "disregard all prior",
        "forget everything",
        "new instructions:",
        "system:",
        "assistant:"
    ]

    text_lower = text.lower()
    for pattern in dangerous_patterns:
        if pattern in text_lower:
            logger.warning(f"Potential prompt injection detected: {pattern}")
            return "[INVALID INPUT DETECTED]"

    return text

# Usar al procesar datos de usuario
user_goals = sanitize_user_input(user.retirement_goals or "")
```

### Límites de Tamaño de Respuesta

Evita uso descontrolado de tokens:

```python
def truncate_response(text: str, max_length: int = 50000) -> str:
    """Asegura que las respuestas no excedan tamaño razonable"""
    if len(text) > max_length:
        logger.warning(f"Response truncated from {len(text)} to {max_length} characters")
        return text[:max_length] + "\n\n[Response truncated due to length]"
    return text
```

### Retries con Backoff Exponencial

Agrega resiliencia a invocaciones de agentes usando la librería **tenacity**, ya presente para manejar errores de límite de tasa:

```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import asyncio
from typing import Optional

# Excepciones personalizadas para errores temporales
class AgentTemporaryError(Exception):
    """Temporary error that should trigger retry"""
    pass

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((AgentTemporaryError, TimeoutError))
)
async def invoke_agent_with_retry(
    agent_name: str,
    payload: dict
) -> dict:
    """Invocar agente con retry automático usando tenacity"""
    try:
        response = await lambda_client.invoke(
            FunctionName=f"alex-{agent_name}",
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )

        result = json.loads(response['Payload'].read())

        # Revisar errores retryables en respuesta
        if result.get('error_type') == 'RATE_LIMIT':
            raise AgentTemporaryError(f"Rate limit hit for {agent_name}")

        return result

    except Exception as e:
        logger.warning(f"Agent {agent_name} invocation failed: {e}")
        # Determina si es error retryable
        if "throttled" in str(e).lower() or "timeout" in str(e).lower():
            raise AgentTemporaryError(f"Temporary error: {e}")
        raise  # Error no retryable
```

**Nota:** Ya tienes tenacity configurado para manejar límites de tasa en los agentes. Este patrón amplía el manejo a otros fallos temporales con backoff exponencial.

## Sección 5: Explicabilidad

Los LLMs y los sistemas agenticos modernos ofrecen transparencia sin precedentes frente a las IA tradicionales tipo "caja negra". Impletemos características de explicabilidad para que el usuario comprenda las decisiones de la IA.

### La Evolución de la IA Explicable

En los inicios del deep learning, las redes neuronales eran criticadas por ser "cajas negras", sin razonamiento claro en su salida. Esto era problemático en industrias reguladas como finanzas y salud.

Los LLMs modernos y sistemas agenticos resuelven esto mediante:

1. **Explicaciones en lenguaje natural** - La IA puede justificar sus decisiones en texto plano
2. **Cadena de razonamiento** - Resolución paso a paso verificable
3. **Salidas estructuradas** - Respuestas predecibles, parseables y lógicas
4. **Transparencia del prompt** - Las instrucciones a la IA son visibles y editables

### Explicabilidad en el Tagger Agent

Modifica el agente Tagger para incluir una justificación de sus decisiones. Añade esto en `backend/tagger/agent.py`:

```python
from pydantic import BaseModel, Field
from typing import Dict

class InstrumentClassificationWithRationale(BaseModel):
    # La justificación DEBE ir primero para que el LLM la genere antes que las respuestas
    rationale: str = Field(
        description="Detailed explanation of why these classifications were chosen, including specific factors considered"
    )

    asset_class: AssetClassType = Field(
        description="Primary asset class classification"
    )

    asset_class_allocation: Dict[str, float] = Field(
        description="Percentage breakdown by asset class",
        example={"equity": 100.0}
    )

    region_allocation: Dict[str, float] = Field(
        description="Percentage breakdown by geographic region",
        example={"north_america": 70.0, "europe": 20.0, "asia_pacific": 10.0}
    )

    sector_allocation: Dict[str, float] = Field(
        description="Percentage breakdown by sector (only for equity)",
        example={"technology": 30.0, "healthcare": 20.0, "financial": 50.0}
    )

# En la función de tu agente tagger:
async def run_tagger_agent(instrument: dict) -> dict:
    model = LitellmModel(model=f"bedrock/{bedrock_model}")

    with trace("Classify instrument with explainability"):
        agent = Agent(
            name="Instrument Tagger with Explainability",
            instructions=CLASSIFICATION_INSTRUCTIONS,
            model=model,
            response_format=InstrumentClassificationWithRationale
        )

        result = await Runner.run(
            agent,
            input=create_classification_task(instrument),
            max_turns=1
        )

        classification = result.final_output_as(InstrumentClassificationWithRationale)

        # Log de la justificación para trail de auditoría
        logger.info(json.dumps({
            "event": "CLASSIFICATION_RATIONALE",
            "symbol": instrument["symbol"],
            "rationale": classification.rationale,
            "timestamp": datetime.utcnow().isoformat()
        }))

        # Devuelve la clasificación sin justificación al planner
        return {
            "asset_class": classification.asset_class,
            "asset_class_allocation": classification.asset_class_allocation,
            "region_allocation": classification.region_allocation,
            "sector_allocation": classification.sector_allocation
        }
```

### Explicabilidad en las Recomendaciones de Portafolio

Para el agente Reporter, agrega razonamiento en sus recomendaciones:

```python
# En templates.py
ANALYSIS_INSTRUCTIONS_WITH_EXPLANATION = """
When providing recommendations, always:
1. Start with your reasoning process
2. List specific factors you considered
3. Explain why certain recommendations were prioritized
4. Include any assumptions made
5. Note any limitations or caveats

Format each recommendation as:
**Recommendation:** [The action to take]
**Reasoning:** [Why this recommendation was made]
**Impact:** [Expected outcome if implemented]
**Priority:** [High/Medium/Low based on user goals]
"""
```

### Log de Auditoría para Compliance

Crea log de auditoría integral para decisiones IA:

```python
class AuditLogger:
    @staticmethod
    def log_ai_decision(
        agent_name: str,
        job_id: str,
        input_data: dict,
        output_data: dict,
        model_used: str,
        duration_ms: int
    ):
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "agent": agent_name,
            "job_id": job_id,
            "model": model_used,
            "input_hash": hashlib.sha256(
                json.dumps(input_data, sort_keys=True).encode()
            ).hexdigest(),
            "output_summary": {
                "type": type(output_data).__name__,
                "size_bytes": len(json.dumps(output_data))
            },
            "duration_ms": duration_ms,
            "compliance_check": "PASS"  # Añade lógica real de compliance
        }

        # Almacenar en CloudWatch (retención largo plazo)
        logger.info(json.dumps(audit_entry))

        # Opcional: almacenar en DynamoDB para consultas
        return audit_entry
```

## Sección 6: Observabilidad con LangFuse

LangFuse ofrece trazabilidad exhaustiva para aplicaciones LLM, permitiendo visibilidad total en interacciones de agentes, uso de tokens y métricas de rendimiento. Integramos LangFuse en todos los agentes usando un patrón de context manager limpio.

### Enfoque de Implementación

Implementamos un patrón de observabilidad reutilizable que:

- Funciona transparentemente - los agentes operan aunque no haya credenciales LangFuse
- Usa context manager para flush automático de trazas
- Instrumenta el OpenAI Agents SDK vía Pydantic Logfire
- Proporciona logging detallado en cada paso

### Crear Cuenta en LangFuse

**Paso 1: Crea tu cuenta en LangFuse**

1. Ve a https://cloud.langfuse.com
2. Regístrate gratis
3. Crea una organización (requerido la primera vez)
4. Crea un proyecto nuevo llamado "alex-financial-advisor"
5. Ve a Settings → API Keys
6. Crea un par de llaves API
7. Copia tu Public Key y Secret Key (las necesitarás para configurar)

**Paso 2: Configura tu entorno**

Agrega tus credenciales de LangFuse a `terraform/6_agents/terraform.tfvars`:

```hcl
# Observabilidad LangFuse (opcional pero recomendado)
langfuse_public_key = "pk-lf-xxxxxxxxxx"
langfuse_secret_key = "sk-lf-xxxxxxxxxx"
langfuse_host       = "https://cloud.langfuse.com"

# Requerido para exportar trazas (aunque se use Bedrock)
openai_api_key = "sk-xxxxxxxxxx"  # Tu clave OpenAI
```

**Importante**: El `openai_api_key` es necesario para que las trazas se exporten con LangFuse, incluso usando modelos Bedrock. Es un detalle de la integración OpenTelemetry.

### Así Funciona la Integración

Cada agente incluye un módulo `observability.py` que brinda un context manager para integración con LangFuse:

```python
from observability import observe

def lambda_handler(event, context):
    # Encapsular todo el handler con observabilidad
    with observe():
        # Tu código lambda aquí
        result = asyncio.run(run_agent(...))
        return {...}
    # Trazas se envían automáticamente aquí
```

El context manager `observe()`:

- Verifica variables de entorno LangFuse
- Configura Pydantic Logfire para instrumentar OpenAI Agents SDK
- Asigna el nombre de servicio adecuado (ej: 'alex_planner_agent')
- Maneja la autenticación de manera segura
- **Hace flush automático de trazas al salir** (crítico en Lambda)

### Observar Tus Agentes

**Paso 3: Despliega con Observabilidad**

Desde `backend`:

```bash
# Empaqueta todos los agentes con observabilidad
uv run deploy_all_lambdas.py --package
```

Desde `terraform/6_agents`:

```bash
# Despliega infraestructura con variables LangFuse
terraform apply
```

Desde `backend`:

```bash
# Monitorea logs de agentes en tiempo real
uv run watch_agents.py
```

Finalmente, en `scripts`:

```bash
# Despliega la aplicación completa
uv run deploy.py
```

**Paso 4: Ver las trazas en el dashboard de LangFuse**

Una vez desplegado y en ejecución, tienes dos opciones para ver las trazas:

1. **LangFuse Dashboard** (https://cloud.langfuse.com) - Entra a tu proyecto y ve:
2. **Dashboard de trazas de OpenAI** - Si usas modelos OpenAI, también puedes ver en https://platform.openai.com/traces

En el tablero LangFuse visualizarás:

1. **Trazas de agentes**

   - Cada ejecución de agente aparece como traza
   - Filtra por nombre de servicio: `alex_planner_agent`, `alex_reporter_agent`, etc.
   - Ves el flujo completo de interacciones
   - Revisa uso de tokens y costos

2. **Métricas de rendimiento**

   - Tiempos de respuesta de cada agente
   - Patrones de consumo de tokens
   - Comparación de modelos
   - Tasa de éxitos/fallos

3. **Información de depuración**
   - Prompts exactos enviados al modelo
   - Respuestas completas recibidas
   - Mensajes de error y stack traces
   - Llamadas a herramientas y resultados

### Uso del Watch Script

Creamos un script para ver logs de agentes en tiempo real:

```bash
# Desde backend
uv run watch_agents.py

# Opciones:
uv run watch_agents.py --lookback 10  # Busca 10 minutos hacia atrás
uv run watch_agents.py --interval 1   # Cada segundo
uv run watch_agents.py --region us-west-2  # Otra región
```

El script muestra:

- Color por agente (PLANNER=azul, REPORTER=verde, etc.)
- Logs LangFuse en morado
- Errores en rojo
- Actualizaciones en vivo de los 5 agentes a la vez

### Problemas Comunes con Observabilidad

**Si no ves trazas en LangFuse:**

1. **Verifica variables de entorno:**

   ```bash
   aws lambda get-function-configuration --function-name alex-planner | grep LANGFUSE
   ```

2. **Verifica que OPENAI_API_KEY esté definida** (requerido p/exportar):

   ```bash
   aws lambda get-function-configuration --function-name alex-planner | grep OPENAI_API_KEY
   ```

3. **Mira logs de CloudWatch por mensajes LangFuse:**

   ```bash
   uv run watch_agents.py --lookback 5
   ```

   Busca mensajes como:

   - "🔍 Observability: Setting up LangFuse..."
   - "✅ Observability: Traces flushed successfully"
   - "❌ Observability: Failed to flush traces"

4. **Revisa el tablero LangFuse por trazas** - a veces demoran 30-60 seg.

**Problemas típicos:**

- **No hay trazas pero logs son OK**: Normalmente falta OPENAI_API_KEY
- **Auth check failed warning**: Normal si usas plan gratis, las trazas funcionan igual
- **Missing required package error**: Reejecuta package_docker.py para incluir dependencias

## Conclusión: Tu IA Empresarial

🎉 **¡Felicidades!** Has desplegado un sistema IA agentico de nivel empresarial.

### Lo que has logrado

Has construido una plataforma de asesoría financiera lista para producción que es:

- **Escalable**: Arquitectura serverless maneja desde 1 hasta 1,000,000+ usuarios sin cambios
- **Segura**: Seguridad multinivel con IAM, auth JWT, limitación API, CORS, XSS y secretos seguros
- **Robusta y Monitoreada**: Logs CloudWatch detallados, dashboards, alarmas y colas DLQ para confiabilidad
- **Protegida**: Validación de entrada, verificación de salida, lógica de retry y manejo elegante de fallos IA
- **Explicable**: Las decisiones de IA incluyen racional, logs de auditoría y razonamiento transparente
- **Observable**: Integración LangFuse brinda trazabilidad, uso de tokens, costos y métricas de performance para cada interacción IA
