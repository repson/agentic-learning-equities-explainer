# Resumen de trabajo realizado

Fecha: 2026-05-23

## Objetivo general

Se reforzo el proyecto Alex en tres frentes principales:

- Estabilidad operativa (errores AWS, reintentos, validaciones)
- Observabilidad y auditoria (logs estructurados y trazabilidad)
- Seguridad y control de salida (sanitizacion y truncado)

## Problemas encontrados y solucion

### 1) Error Bedrock `InvokeModel` (AccessDenied)

Problema:

- Lambda `alex-planner` fallaba con `bedrock:InvokeModel` no autorizado.
- El error mostraba recurso en `eu-west-3` aunque la Lambda estaba en `eu-west-1`.

Causa raiz:

- Uso de `eu.amazon.nova-pro-v1:0` (profile regional EU), que puede enrutar a varias regiones.
- Politica IAM insuficiente para el rol `alex-lambda-agents-role`.

Solucion aplicada:

- Revisar region efectiva y variables de entorno en Lambda.
- Ajustar permisos Bedrock para permitir invocacion del modelo/profile usado.
- Confirmar uso de `AWS_REGION_NAME` para LiteLLM.

### 2) Reporte incompleto por error de carga de usuario

Problema:

- CloudWatch mostraba: `'in <string>' requires string as left operand, not dict`.

Causa raiz:

- Bug en `backend/reporter/lambda_handler.py`:
  - `if job in job.get("clerk_user_id"):`

Solucion aplicada:

- Corregido a:
  - `if job and job.get("clerk_user_id"):`

### 3) Falla de FK en test de multiples cuentas

Problema:

- `positions_symbol_fkey` al insertar posiciones en `test_multiple_accounts.py`.

Causa raiz:

- Se insertaban simbolos no presentes en `instruments` (`VEA`, `TSLA`, `ARKK`).

Solucion aplicada:

- Se agregaron esos simbolos al bloque de creacion de instrumentos del test.

### 4) `watch_agents.py` no encontraba grupos de logs

Problema:

- Mensaje repetido: "Grupo de logs ... no encontrado".

Causa raiz:

- El script usa `us-east-1` por defecto, pero los logs estan en `eu-west-1`.

Solucion aplicada:

- Ejecutar con:
  - `uv run watch_agents.py --region eu-west-1`

## Cambios implementados

### A) Observabilidad enterprise (logs estructurados)

- API:
  - `backend/api/main.py`
  - Eventos: `ANALYSIS_TRIGGERED`, `ANALYSIS_ENQUEUED`, `ANALYSIS_NOT_ENQUEUED`

- Agentes:
  - `backend/planner/lambda_handler.py`
  - `backend/tagger/lambda_handler.py`
  - `backend/reporter/lambda_handler.py`
  - `backend/charter/lambda_handler.py`
  - `backend/retirement/lambda_handler.py`

Se anadieron eventos de inicio/fin, estado (success/failed), duracion y metadatos clave.

### B) Validacion de salida en Charter

- `backend/charter/agent.py`
  - Nueva funcion `validate_chart_data(...)` para validar JSON de salida.

- `backend/charter/lambda_handler.py`
  - Integracion de la validacion antes de persistir graficas.
  - Fallback seguro si el JSON no es valido.

### C) Sanitizacion contra prompt injection en todos los agentes

Se agrego `sanitize_user_input(...)` y su uso en:

- `backend/planner/agent.py`
- `backend/reporter/agent.py`
- `backend/retirement/agent.py`
- `backend/tagger/agent.py`
- `backend/charter/agent.py`

### D) Control de longitud de respuesta

Se agrego `truncate_response(...)` para limitar salidas excesivas en:

- `backend/reporter/lambda_handler.py`
- `backend/retirement/lambda_handler.py`
- `backend/charter/lambda_handler.py`
- `backend/planner/lambda_handler.py`

Nota: esto limita tamano de salida almacenada/logueada; no reduce por si solo tokens ya consumidos por inferencia.

### E) Resiliencia en invocaciones entre agentes con Tenacity

- `backend/planner/agent.py`
  - Nueva excepcion `AgentTemporaryError`
  - Nueva funcion `invoke_agent_with_retry(...)`
  - Reintentos exponenciales para errores temporales (throttle/timeout/rate limit)
  - Integrado en invocaciones a `reporter`, `charter`, `retirement` y `tagger`.

### F) Auditoria integral de decisiones IA

- Nuevo archivo:
  - `backend/database/src/audit.py`
  - Clase `AuditLogger.log_ai_decision(...)`

- Exportado en:
  - `backend/database/src/__init__.py`

- Integrado en:
  - `backend/planner/lambda_handler.py`
  - `backend/tagger/lambda_handler.py`
  - `backend/reporter/lambda_handler.py`
  - `backend/charter/lambda_handler.py`
  - `backend/retirement/lambda_handler.py`

Incluye hash de input, resumen de output, modelo, duracion y check de compliance.

### G) Explicabilidad en Tagger y Reporter

- `backend/tagger/agent.py`
  - `InstrumentClassification` ahora incluye `rationale`.
  - Log de auditoria `CLASSIFICATION_RATIONALE` por simbolo.

- `backend/reporter/templates.py`
  - Se agrego `ANALYSIS_INSTRUCTIONS_WITH_EXPLANATION`.
  - Se incorporaron instrucciones para que recomendaciones incluyan razonamiento, impacto y prioridad.

## Commits realizados

- `6843d39` Fix reporter user-data check and seed missing test symbols
- `4c8bd41` Add structured enterprise logging across API and agents
- `fd21f1f` Add input sanitization and charter output validation
- `f4c016f` Add retry resilience and response truncation safeguards
- `f19851a` Add AI audit logging and reasoning enhancements
- `1659fd7` Remove stale Terraform lock artifacts

## Estado actual

- Cambios de codigo: comprometidos en git.
- Pendiente en working tree: solo directorios `__pycache__/` sin trackear.

## Recomendaciones siguientes

1. Actualizar `watch_agents.py` para que tome por defecto `DEFAULT_AWS_REGION` y evite errores de region.
2. Agregar `__pycache__/` a `.gitignore` del repo si no esta ya cubierto.
3. Ejecutar prueba E2E (`uv run test_full.py`) y revisar en CloudWatch los eventos de auditoria y observabilidad.
