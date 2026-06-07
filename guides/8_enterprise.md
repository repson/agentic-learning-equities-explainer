# Guide 8: Enterprise Level - Scalability, Security, Monitoring, Guardrails, and Observability

Welcome to the final guide in the Alex Financial Advisor deployment series! In this guide, we will transform our application into a production-ready, enterprise-capable system by implementing best practices for scalability, security, monitoring, guardrails, explainability, and observability.

By the end of this guide, your Alex Financial Advisor will be:

- **Scalable**: Ready to handle enterprise-grade traffic
- **Secure**: Protected with multiple security layers
- **Monitored**: Full visibility into system health and performance
- **Protected**: Safeguarded against AI hallucinations and errors
- **Explainable**: AI decision-making is transparent
- **Observable**: End-to-end traceability for all agent interactions

## REMINDER - IMPORTANT TIP!

There is a `gameplan.md` file at the project root that describes the full Alex project for an AI Agent, so you can ask questions and get help. There is also an identical `CLAUDE.md` and `AGENTS.md` file. If you need help, just start your favorite AI Agent and give it this instruction:

> I am a student in the AI in Production course. We are in the course repository. Read the `gameplan.md` file to get the project overview. Read this file completely and read all linked guides carefully. Do not start any work besides reading and reviewing the directory structure. When you finish all reading, let me know if you have any questions before we begin.

After answering questions, state exactly which guide you are on and any issue you are facing. Be careful when validating each suggestion; always ask for the root cause and evidence behind problems. LLMs tend to jump to conclusions, but they often correct themselves when they must provide evidence.

## Section 1: Scalability

Our serverless architecture is already designed for automatic scaling, but let's explore how to tune it for enterprise-level traffic.

### Understanding Serverless Scalability

The advantage of our serverless architecture is that AWS automatically scales components based on demand:

1. **Lambda functions** scale automatically:

   - Concurrent executions: 1,000 by default (can increase to 10,000+)
   - Each agent can handle multiple requests simultaneously
   - No server management required

2. **Aurora Serverless v2** scales automatically:

   - From 0.5 to 1 ACU (Aurora Capacity Units) by default
   - Can scale up to 128 ACUs for high traffic
   - Scales in ~15 seconds based on load

3. **API Gateway** handles millions of requests:

   - Default limit: 10,000 requests/second
   - Burst: 5,000 requests
   - Can be increased through AWS Support

4. **SQS** provides virtually unlimited throughput:
   - Standard queues: nearly unlimited TPS
   - FIFO queues: 300 messages/second (batching can raise this to 3,000)

### Configuration for Higher Scalability

To prepare for enterprise traffic, you can adjust these parameters in Terraform configs:

**In `terraform/5_database/main.tf`:**

```hcl
resource "aws_rds_cluster" "aurora" {
  # Increase max capacity for high traffic
  serverlessv2_scaling_configuration {
    max_capacity = 16  # Increase from 1 to 16 ACUs
    min_capacity = 0.5 # Keep minimum low for cost efficiency
  }
}
```

**In `terraform/6_agents/main.tf`:**

```hcl
resource "aws_lambda_function" "planner" {
  # Increase memory to process faster
  memory_size = 10240  # Increase from 3072 to 10GB
  timeout     = 900    # Keep max at 15 minutes

  # Add reserved concurrency for guaranteed capacity
  reserved_concurrent_executions = 100  # Guarantee 100 concurrent executions
}
```

**In `terraform/7_frontend/main.tf`:**

```hcl
resource "aws_apigatewayv2_stage" "api" {
  # Configure throttling for protection
  default_route_settings {
    throttle_rate_limit  = 10000  # Requests per second
    throttle_burst_limit = 5000   # Burst capacity
  }
}
```

### Load Testing Your Application

Before going to production, test your scalability:

**For macOS/Linux:**

```bash
# Install Apache Bench
apt-get install apache2-utils  # Ubuntu/Debian
brew install apache2-utils     # macOS

# Test API endpoint (replace with your API URL)
ab -n 1000 -c 50 -H "Authorization: Bearer YOUR_TOKEN" \
   https://your-api.execute-api.region.amazonaws.com/api/user
```

**For Windows:**

```powershell
# Install Apache Bench via XAMPP or use PowerShell Invoke-WebRequest
# Option 1: Download XAMPP, which includes Apache Bench
# Visit: https://www.apachefriends.org/download.html

# Option 2: Use PowerShell for simple load testing
$headers = @{"Authorization" = "Bearer YOUR_TOKEN"}
$url = "https://your-api.execute-api.region.amazonaws.com/api/user"

# Run 100 sequential requests
1..100 | ForEach-Object {
    Invoke-WebRequest -Uri $url -Headers $headers -Method GET
    Write-Host "Request $_ completed"
}

# For concurrent requests, consider a tool like JMeter (cross-platform)
# Download from: https://jmeter.apache.org/download_jmeter.cgi
```

### Cost Optimization at Scale

Monitor and optimize costs as you scale:

1. **Use AWS Cost Explorer** to track spending
2. **Set billing alerts** for unexpected costs
3. **Optimize CloudFront caching** - CloudFront already caches static content from your S3 bucket automatically, but you can improve performance and reduce costs by tuning cache behavior. Set longer TTLs for assets that rarely change (images, CSS, JS) with Cache-Control headers. This reduces origin requests (S3), lowers transfer costs, and improves response times.
4. **Consider Step Functions** for complex orchestration at scale

## Section 2: Security

Our application already implements several security best practices. Let's review them and explore additional enterprise security features.

### Current Security Implementation

#### 1. **Least-Privilege IAM Access**

Each Lambda function has only the minimum required permissions:

```hcl
# In terraform/6_agents/main.tf
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

#### 2. **JWT Authentication with Clerk**

All API calls require valid JWT tokens:

- Tokens expire after 1 hour
- **JWKS endpoint for key rotation** - Clerk automatically rotates signing keys for security. The JWKS (JSON Web Key Set) endpoint provides current public keys used to verify JWT signatures. This means if a key is compromised, it rotates automatically and your app gets updated keys without code changes.
- **User context validated on every request** - Every call includes a JWT token cryptographically verified using Clerk public keys. This ensures the user is who they claim to be, their session is still valid, and the token was not tampered with. Invalid or expired tokens are rejected before any business logic runs.

#### 3. **API Gateway Throttling**

**Protection against DDoS and abuse** - DDoS (Distributed Denial of Service) attacks try to overwhelm your application with many requests. API Gateway throttling limits requests per second and automatically rejects excess traffic. This protects your Lambdas and prevents runaway costs caused by malicious traffic:

```hcl
throttle_rate_limit  = 100   # 100 requests per second per user
throttle_burst_limit = 200   # Burst capacity
```

#### 4. **CORS Control**

Strict CORS configuration:

- **Origin validation** - Allows requests only from your specific frontend domain, preventing malicious sites from making calls on behalf of users
- **No credentials with wildcard origins** - Prevents credential theft by ensuring auth cookies/tokens are only sent to explicitly trusted origins
- **Preflight caching for performance** - The browser caches preflight responses, reducing OPTIONS requests and improving API responsiveness

#### 5. **XSS Protection**

**Cross-Site Scripting (XSS) prevention** - XSS attacks inject malicious scripts into your pages that execute in the user's browser, stealing credentials or personal data. Content Security Policy (CSP) headers tell the browser which content sources are trusted, blocking unauthorized scripts:

```javascript
// In frontend pages
<meta
  httpEquiv="Content-Security-Policy"
  content="default-src 'self'; script-src 'self' 'unsafe-inline' https://clerk.com; style-src 'self' 'unsafe-inline';"
/>
```

#### 6. **Secret Management**

Using AWS Secrets Manager:

- Database credentials are never in code
- Automatic rotation is available
- Encryption at rest with KMS

**To view your secrets:** Go to AWS Console -> Secrets Manager -> Select your region (us-east-1) -> You will see secrets like `alex-database-secret` with Aurora credentials

### Additional Enterprise Security Features

To strengthen security even further, consider implementing:

#### 1. **AWS WAF (Web Application Firewall)**

**AWS WAF** adds another protection layer by filtering malicious web traffic before it reaches your application. It protects against known attacks such as SQL Injection, XSS, and bots. WAF uses rules to inspect each request and can block, allow, or count requests based on defined conditions. It is a paid add-on service, billed by rules and request volume.

Add in `terraform/7_frontend/main.tf`:

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

#### 2. **VPC Endpoints for Private Communication**

**VPC Endpoints** let your Lambdas communicate with AWS services without traffic going over the public internet. This improves security, reduces data transfer costs, and lowers latency. VPC endpoints are free to create, with data processing charged (~$0.01/GB). They are ideal in high-security environments where data must never leave AWS.

Keep traffic inside AWS:

```hcl
resource "aws_vpc_endpoint" "s3" {
  vpc_id       = aws_vpc.main.id
  service_name = "com.amazonaws.region.s3"
}
```

#### 3. **AWS GuardDuty for Threat Detection**

**AWS GuardDuty** is a managed threat detection service that monitors accounts and workloads for malicious activity. It uses machine learning over VPC Flow Logs, CloudTrail events, and DNS logs to detect crypto mining, credential theft, unusual API calls, and more. It requires no infrastructure, but it is paid (~$1 per GB of analyzed logs). It is very useful for detecting sophisticated attacks that may bypass other layers.

```hcl
resource "aws_guardduty_detector" "main" {
  enable = true
  finding_publishing_frequency = "FIFTEEN_MINUTES"
}
```

#### 4. **Parameter Validation**

Add to Lambdas:

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

## Section 3: Monitoring

Let's improve logging and create CloudWatch dashboards to monitor the app.

### Improved Logging Implementation

First, let's make sure agents and API have complete logs:

**For API (`backend/api/main.py`):**

```python
import logging
import json
from datetime import datetime

# Configure structured logging
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

# Add to endpoint
@app.post("/api/analyze")
async def trigger_analysis(user=Depends(clerk_guard)):
    StructuredLogger.log_event(
        "ANALYSIS_TRIGGERED",
        user_id=user.clerk_user_id,
        details={"accounts": user_id}
    )
    # ... rest of endpoint
```

**For agents (example in `backend/planner/lambda_handler.py`):**

```python
import logging
import json
from datetime import datetime, timezone

logger = logging.getLogger()
logger.setLevel(logging.INFO)

async def run_orchestrator(job_id: str) -> None:
    start_time = datetime.now(timezone.utc)

    # Get the job to log who made the request
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

    # ... perform tagging, price updates, etc. ...

    for agent_name in ["reporter", "charter", "retirement"]:
        logger.info(json.dumps({
            "event": "AGENT_INVOKED",
            "agent": agent_name,
            "job_id": job_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }))

    # ... run planner agent with Runner.run(...) ...

    end_time = datetime.now(timezone.utc)
    logger.info(json.dumps({
        "event": "PLANNER_COMPLETED",
        "job_id": job_id,
        "duration_seconds": (end_time - start_time).total_seconds(),
        "status": "success",
        "timestamp": end_time.isoformat(),
    }))
```

### Deploying and Verifying Logging Changes

After adding structured logging (you already have it in `backend/planner/lambda_handler.py`), deploy and verify:

1.  **Package the updated code:**

```bash
# Go to backend directory
cd backend

# Run packaging script
uv run package_docker.py
```

2.  **Deploy package to AWS:**

```bash
# From backend
uv run deploy_all_lambdas.py
```

3.  **Launch a new analysis:** Open your CloudFront site and run a new portfolio analysis, then review logs in CloudWatch.

### Create CloudWatch Dashboards

From the Terraform directory, in `8_enterprise`:

Copy `terraform.tfvars.example` to `terraform.tfvars` and update values as usual.

Then:

`terraform init`

`terraform apply`

And follow the instructions to spin up your new CloudWatch dashboards for Bedrock, SageMaker, and agent activity.

#### 3. **SQS Queue Monitoring**

In the SQS console, view:

- Messages in flight
- Message age
- Throughput metrics
- **DLQ (Dead Letter Queue) monitoring** - Failed messages automatically go to the DLQ after multiple retries. Monitor the DLQ to detect failure patterns. Configure CloudWatch alarms when messages appear so you can investigate quickly.

### CloudWatch Alarm Configuration

To create alarms for critical metrics, use the AWS Console:

1. **Sign in to AWS Console** as root (or IAM user with CloudWatch permissions)
2. **Go to CloudWatch** -> Click "Alarms" in the left menu -> "Create alarm"
3. **Select metric** -> "Lambda" -> "By Function Name" -> Choose your function (example: alex-api)
4. **Configure alarm:**
   - Metric: Errors
   - Statistic: Sum
   - Period: 5 minutes
   - Threshold: Greater than 5
5. **Set notification** -> New SNS topic -> Enter email -> Confirm by email
6. **Name the alarm** (example: "alex-api-errors") and create it

Repeat for other critical metrics like Duration, Throttles, and Concurrent Executions.

### Cost Monitoring

**You already have billing alerts from previous guides!** Remember to review spending regularly:

1. **AWS Console** -> Billing Dashboard (top-right menu)
2. **Review monthly charges** - Go to "Bills"
3. **Monitor your budget alerts** - You should have alerts at 50%, 80%, and 100%
4. **Use Cost Explorer** for detailed analysis - Filter by service to identify the top cost drivers

**Review costs frequently!** During development and after every deployment; Lambda and API Gateway can become expensive under heavy traffic.

## Section 4: Guardrails

**Guardrails are essential safety mechanisms in AI systems.** While advanced frameworks often include sophisticated guardrails, guardrails are fundamentally validations you implement in code: checks you run before or after agent execution to ensure outputs are safe and correct. The best guardrails are in code, where you have full control over the logic.

Let's implement validations and checks to prevent AI errors from impacting users.

### Charter Agent Output Validation

Add this validation code in `backend/charter/agent.py` to ensure output is well-formed JSON:

```python
import json
import logging
from typing import Dict, Any

logger = logging.getLogger()

def validate_chart_data(chart_json: str) -> tuple[bool, str, Dict[Any, Any]]:
    """
    Validate that charter agent output is well-formed JSON with the expected structure.
    Returns (is_valid, error_message, parsed_data)
    """
    try:
        # Parse JSON
        data = json.loads(chart_json)

        # Validate expected structure
        required_keys = ["charts"]
        if not all(key in data for key in required_keys):
            return False, f"Missing required keys. Expected: {required_keys}", {}

        # Validate charts is an array
        if not isinstance(data["charts"], list):
            return False, "Charts must be an array", {}

        # Validate each chart
        for i, chart in enumerate(data["charts"]):
            if "type" not in chart:
                return False, f"Chart {i} missing 'type' field", {}

            if "data" not in chart:
                return False, f"Chart {i} missing 'data' field", {}

            # Validate data is an array
            if not isinstance(chart["data"], list):
                return False, f"Chart {i} data must be an array", {}

            # Check fields by chart type
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

# Use in your charter agent:
async def run_charter_agent(job_id: str, task: str) -> str:
    # ... existing agent code ...

    result = await Runner.run(agent, input=task, max_turns=10)

    # Validate output
    is_valid, error_msg, parsed_data = validate_chart_data(result.final_output)

    if not is_valid:
        logger.error(f"Charter agent produced invalid output for job {job_id}: {error_msg}")
        # Safe fallback
        return json.dumps({
            "charts": [],
            "error": "Unable to generate charts at this time"
        })

    return json.dumps(parsed_data)
```

### Input Validation Guardrails

Add to all agents to prevent prompt injection:

```python
def sanitize_user_input(text: str) -> str:
    """Remove potential prompt injection attempts"""
    # Remove common injection patterns
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

# Use when processing user data
user_goals = sanitize_user_input(user.retirement_goals or "")
```

### Response Size Limits

Avoid uncontrolled token usage:

```python
def truncate_response(text: str, max_length: int = 50000) -> str:
    """Ensure responses do not exceed a reasonable size"""
    if len(text) > max_length:
        logger.warning(f"Response truncated from {len(text)} to {max_length} characters")
        return text[:max_length] + "\n\n[Response truncated due to length]"
    return text
```

### Retries with Exponential Backoff

Add resilience to agent invocations using the **tenacity** library, already present for rate-limit handling:

```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import asyncio
from typing import Optional

# Custom exceptions for temporary errors
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
    """Invoke agent with automatic retry using tenacity"""
    try:
        response = await lambda_client.invoke(
            FunctionName=f"alex-{agent_name}",
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )

        result = json.loads(response['Payload'].read())

        # Check retryable response errors
        if result.get('error_type') == 'RATE_LIMIT':
            raise AgentTemporaryError(f"Rate limit hit for {agent_name}")

        return result

    except Exception as e:
        logger.warning(f"Agent {agent_name} invocation failed: {e}")
        # Determine if error is retryable
        if "throttled" in str(e).lower() or "timeout" in str(e).lower():
            raise AgentTemporaryError(f"Temporary error: {e}")
        raise  # Non-retryable error
```

**Note:** You already have tenacity configured for agent rate limits. This pattern extends handling to other temporary failures with exponential backoff.

## Section 5: Explainability

Modern LLMs and agentic systems provide unprecedented transparency compared to traditional "black-box" AI. Let's implement explainability features so users can understand AI decisions.

### The Evolution of Explainable AI

In early deep learning, neural networks were criticized as "black boxes" with no clear reasoning behind outputs. This was problematic in regulated industries such as finance and healthcare.

Modern LLMs and agentic systems address this through:

1. **Natural language explanations** - AI can justify decisions in plain text
2. **Reasoning chains** - Step-by-step problem-solving that can be verified
3. **Structured outputs** - Predictable, parseable, logical responses
4. **Prompt transparency** - AI instructions are visible and editable

### Explainability in the Tagger Agent

Modify the Tagger agent to include rationale for decisions. Add this in `backend/tagger/agent.py`:

```python
from pydantic import BaseModel, Field
from typing import Dict

class InstrumentClassificationWithRationale(BaseModel):
    # Rationale MUST come first so the LLM generates it before final answers
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

# In your tagger agent function:
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

        # Log rationale for audit trail
        logger.info(json.dumps({
            "event": "CLASSIFICATION_RATIONALE",
            "symbol": instrument["symbol"],
            "rationale": classification.rationale,
            "timestamp": datetime.utcnow().isoformat()
        }))

        # Return classification without rationale to planner
        return {
            "asset_class": classification.asset_class,
            "asset_class_allocation": classification.asset_class_allocation,
            "region_allocation": classification.region_allocation,
            "sector_allocation": classification.sector_allocation
        }
```

### Explainability in Portfolio Recommendations

For the Reporter agent, add reasoning to recommendations:

```python
# In templates.py
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

### Audit Logging for Compliance

Create comprehensive audit logs for AI decisions:

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
            "compliance_check": "PASS"  # Add real compliance logic
        }

        # Store in CloudWatch (long-term retention)
        logger.info(json.dumps(audit_entry))

        # Optional: store in DynamoDB for querying
        return audit_entry
```

## Section 6: Observability with LangFuse

LangFuse provides full traceability for LLM applications, enabling complete visibility into agent interactions, token usage, and performance metrics. We integrate LangFuse into all agents using a clean context manager pattern.

### Implementation Approach

We implemented a reusable observability pattern that:

- Works transparently - agents operate even without LangFuse credentials
- Uses a context manager for automatic trace flushing
- Instruments OpenAI Agents SDK through Pydantic Logfire
- Provides detailed logging at each step

### Create a LangFuse Account

**Step 1: Create your LangFuse account**

1. Go to https://cloud.langfuse.com
2. Sign up for free
3. Create an organization (required first time)
4. Create a new project named "alex-financial-advisor"
5. Go to Settings -> API Keys
6. Create an API key pair
7. Copy your Public Key and Secret Key (you will need them for configuration)

**Step 2: Configure your environment**

Add your LangFuse credentials to `terraform/6_agents/terraform.tfvars`:

```hcl
# LangFuse observability (optional but recommended)
langfuse_public_key = "pk-lf-xxxxxxxxxx"
langfuse_secret_key = "sk-lf-xxxxxxxxxx"
langfuse_host       = "https://cloud.langfuse.com"

# Required for trace export (even when using Bedrock)
openai_api_key = "sk-xxxxxxxxxx"  # Your OpenAI key
```

**Important**: `openai_api_key` is required for LangFuse trace export, even when using Bedrock models. This is an OpenTelemetry integration detail.

### How the Integration Works

Each agent includes an `observability.py` module that provides a context manager for LangFuse integration:

```python
from observability import observe

def lambda_handler(event, context):
    # Wrap the entire handler with observability
    with observe():
        # Your lambda code here
        result = asyncio.run(run_agent(...))
        return {...}
    # Traces are automatically sent here
```

The `observe()` context manager:

- Checks LangFuse environment variables
- Configures Pydantic Logfire to instrument OpenAI Agents SDK
- Sets the appropriate service name (example: `alex_planner_agent`)
- Handles authentication securely
- **Automatically flushes traces on exit** (critical in Lambda)

### Observing Your Agents

**Step 3: Deploy with observability**

From `backend`:

```bash
# Package all agents with observability
uv run deploy_all_lambdas.py --package
```

From `terraform/6_agents`:

```bash
# Deploy infrastructure with LangFuse variables
terraform apply
```

From `backend`:

```bash
# Monitor agent logs in real time
uv run watch_agents.py
```

Finally, in `scripts`:

```bash
# Deploy the full application
uv run deploy.py
```

**Step 4: View traces in the LangFuse dashboard**

Once deployed and running, you have two options to view traces:

1. **LangFuse Dashboard** (https://cloud.langfuse.com) - Open your project and view traces
2. **OpenAI traces dashboard** - If you use OpenAI models, you can also view traces at https://platform.openai.com/traces

In the LangFuse dashboard you will see:

1. **Agent traces**

   - Each agent run appears as a trace
   - Filter by service name: `alex_planner_agent`, `alex_reporter_agent`, etc.
   - View complete interaction flow
   - Inspect token usage and costs

2. **Performance metrics**

   - Response times per agent
   - Token consumption patterns
   - Model comparison
   - Success/failure rates

3. **Debug information**
   - Exact prompts sent to the model
   - Full responses received
   - Error messages and stack traces
   - Tool calls and results

### Using the Watch Script

We created a script to view agent logs in real time:

```bash
# From backend
uv run watch_agents.py

# Options:
uv run watch_agents.py --lookback 10  # Look back 10 minutes
uv run watch_agents.py --interval 1   # Every second
uv run watch_agents.py --region us-west-2  # Different region
```

The script shows:

- Color by agent (PLANNER=blue, REPORTER=green, etc.)
- LangFuse logs in purple
- Errors in red
- Live updates from all 5 agents at once

### Common Observability Issues

**If you do not see traces in LangFuse:**

1. **Check environment variables:**

   ```bash
   aws lambda get-function-configuration --function-name alex-planner | grep LANGFUSE
   ```

2. **Check `OPENAI_API_KEY` is set** (required for export):

   ```bash
   aws lambda get-function-configuration --function-name alex-planner | grep OPENAI_API_KEY
   ```

3. **Check CloudWatch logs for LangFuse messages:**

   ```bash
   uv run watch_agents.py --lookback 5
   ```

   Look for messages like:

   - "🔍 Observability: Setting up LangFuse..."
   - "✅ Observability: Traces flushed successfully"
   - "❌ Observability: Failed to flush traces"

4. **Check the LangFuse dashboard for traces** - they sometimes take 30-60 seconds to appear.

**Typical issues:**

- **No traces but logs are OK**: Usually missing `OPENAI_API_KEY`
- **Auth check failed warning**: Normal on free plan, traces still work
- **Missing required package error**: Re-run `package_docker.py` to include dependencies

## Conclusion: Your Enterprise AI

🎉 **Congratulations!** You have deployed an enterprise-grade agentic AI system.

### What You Achieved

You built a production-ready financial advisory platform that is:

- **Scalable**: Serverless architecture handles from 1 to 1,000,000+ users without changes
- **Secure**: Multi-layer security with IAM, JWT auth, API throttling, CORS, XSS protection, and secure secrets
- **Robust and Monitored**: Detailed CloudWatch logs, dashboards, alarms, and DLQ queues for reliability
- **Protected**: Input validation, output verification, retry logic, and graceful handling of AI failures
- **Explainable**: AI decisions include rationale, audit logs, and transparent reasoning
- **Observable**: LangFuse integration provides traceability, token usage, costs, and performance metrics for every AI interaction
