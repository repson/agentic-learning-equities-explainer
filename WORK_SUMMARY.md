# Summary of work completed

Date: 2026-05-23

## Overall objective

The Alex project was strengthened across three main areas:

- Operational stability (AWS errors, retries, validations)
- Observability and auditing (structured logs and traceability)
- Security and output control (sanitization and truncation)

## Issues found and solutions

### 1) Bedrock `InvokeModel` error (AccessDenied)

Problem:

- Lambda `alex-planner` failed with unauthorized `bedrock:InvokeModel`.
- The error showed a resource in `eu-west-3` even though the Lambda was in `eu-west-1`.

Root cause:

- Use of `eu.amazon.nova-pro-v1:0` (regional EU profile), which can route across multiple regions.
- IAM policy was insufficient for role `alex-lambda-agents-role`.

Applied solution:

- Review effective region and environment variables in Lambda.
- Adjust Bedrock permissions to allow invocation of the model/profile in use.
- Confirm usage of `AWS_REGION_NAME` for LiteLLM.

### 2) Incomplete report due to user loading error

Problem:

- CloudWatch showed: `'in <string>' requires string as left operand, not dict`.

Root cause:

- Bug in `backend/reporter/lambda_handler.py`:
  - `if job in job.get("clerk_user_id"):`

Applied solution:

- Fixed to:
  - `if job and job.get("clerk_user_id"):`

### 3) FK failure in multi-account test

Problem:

- `positions_symbol_fkey` when inserting positions in `test_multiple_accounts.py`.

Root cause:

- Symbols not present in `instruments` were being inserted (`VEA`, `TSLA`, `ARKK`).

Applied solution:

- Those symbols were added to the test instrument creation block.

### 4) `watch_agents.py` could not find log groups

Problem:

- Repeated message: "Log group ... not found".

Root cause:

- The script uses `us-east-1` by default, but logs are in `eu-west-1`.

Applied solution:

- Run with:
  - `uv run watch_agents.py --region eu-west-1`

## Implemented changes

### A) Enterprise observability (structured logs)

- API:
  - `backend/api/main.py`
  - Events: `ANALYSIS_TRIGGERED`, `ANALYSIS_ENQUEUED`, `ANALYSIS_NOT_ENQUEUED`

- Agents:
  - `backend/planner/lambda_handler.py`
  - `backend/tagger/lambda_handler.py`
  - `backend/reporter/lambda_handler.py`
  - `backend/charter/lambda_handler.py`
  - `backend/retirement/lambda_handler.py`

Start/end events, status (success/failed), duration, and key metadata were added.

### B) Output validation in Charter

- `backend/charter/agent.py`
  - New function `validate_chart_data(...)` to validate output JSON.

- `backend/charter/lambda_handler.py`
  - Validation integrated before persisting charts.
  - Safe fallback if JSON is invalid.

### C) Prompt injection sanitization in all agents

`sanitize_user_input(...)` and its usage were added in:

- `backend/planner/agent.py`
- `backend/reporter/agent.py`
- `backend/retirement/agent.py`
- `backend/tagger/agent.py`
- `backend/charter/agent.py`

### D) Response length control

`truncate_response(...)` was added to limit excessive outputs in:

- `backend/reporter/lambda_handler.py`
- `backend/retirement/lambda_handler.py`
- `backend/charter/lambda_handler.py`
- `backend/planner/lambda_handler.py`

Note: this limits stored/logged output size; it does not by itself reduce tokens already consumed by inference.

### E) Resilience in cross-agent invocations with Tenacity

- `backend/planner/agent.py`
  - New exception `AgentTemporaryError`
  - New function `invoke_agent_with_retry(...)`
  - Exponential retries for temporary errors (throttle/timeout/rate limit)
  - Integrated for invocations to `reporter`, `charter`, `retirement`, and `tagger`.

### F) End-to-end auditing of AI decisions

- New file:
  - `backend/database/src/audit.py`
  - Class `AuditLogger.log_ai_decision(...)`

- Exported in:
  - `backend/database/src/__init__.py`

- Integrated in:
  - `backend/planner/lambda_handler.py`
  - `backend/tagger/lambda_handler.py`
  - `backend/reporter/lambda_handler.py`
  - `backend/charter/lambda_handler.py`
  - `backend/retirement/lambda_handler.py`

Includes input hash, output summary, model, duration, and compliance check.

### G) Explainability in Tagger and Reporter

- `backend/tagger/agent.py`
  - `InstrumentClassification` now includes `rationale`.
  - Audit log `CLASSIFICATION_RATIONALE` per symbol.

- `backend/reporter/templates.py`
  - Added `ANALYSIS_INSTRUCTIONS_WITH_EXPLANATION`.
  - Added instructions so recommendations include reasoning, impact, and priority.
