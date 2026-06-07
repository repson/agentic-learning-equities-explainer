# Alex - "AI in Production" Course Project Guide

## Project Overview

**Alex** (Agentic Learning Equities eXplainer) is a multi-agent enterprise financial planning SaaS platform. This is the final project for Weeks 3 and 4 of the "AI in Production" course taught by Juan Gabriel Gomila at Frogames Formacion, where agent-based solutions are brought to production.

The user is a student in the course. You are working with the user to help them build Alex successfully. The user is working in Cursor (the VS Code fork) and may be on a Windows PC, Mac (Intel or Apple silicon), or Linux machine. All Python code runs with uv, and there are uv projects in every directory that needs it. The student is familiar with AWS services (Lambda, App Runner, Cloudfront) and has been introduced to Terraform, uv, NextJS, and Docker. They have budget alerts configured, but should still review AWS billing screens regularly to control costs.

The student has an AWS root user, and also an IAM user called "aiengineer" with permissions. They have run `aws configure` and should sign in as the aiengineer user with their default region.

### What will students build?

Students will deploy a complete production AI system with:
- **Multi-agent collaboration**: 5 specialized AI agents working together through orchestration
- **Serverless architecture**: Lambda, Aurora Serverless v2, App Runner, API Gateway, SQS
- **Cost-optimized vector storage**: S3 Vectors (90% cheaper than OpenSearch!)
- **Real-time financial analysis**: Portfolio management, retirement projections, market research
- **Production-level practices**: Observability, guardrails, security, monitoring
- **Full-stack application**: React NextJS frontend with Clerk authentication

### Learning Objectives

By completing this project, students will:
1. Deploy and manage production AI infrastructure on AWS
2. Implement multi-agent systems using the OpenAI Agents SDK
3. Integrate AWS Bedrock (with the Nova Pro model) for LLM capabilities
4. Build cost-effective vector search with S3 Vectors and SageMaker embeddings
5. Create serverless agent orchestration with SQS and Lambda
6. Deploy a complete full-stack SaaS application
7. Implement enterprise features: monitoring, observability, guardrails, security

### Commercial Product

Alex is a SaaS product that provides insights about user equity portfolios through reports and charts. Alex is integrated with Clerk for user management, and the database architecture keeps user data separated.

---

## Directory Structure

```
alex/
├── guides/              # Step-by-step deployment guides (START HERE)
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
├── backend/             # Agent and Lambda function code
│   ├── planner/         # Orchestrator agent
│   ├── tagger/          # Instrument classification agent
│   ├── reporter/        # Portfolio analysis agent
│   ├── charter/         # Visualization agent
│   ├── retirement/      # Retirement projection agent
│   ├── researcher/      # Market research agent (App Runner)
│   ├── ingest/          # Document ingestion Lambda
│   ├── database/        # Shared database library
│   └── api/             # FastAPI backend for frontend
│
├── frontend/            # React NextJS application
│   ├── pages/
│   ├── components/
│   └── lib/
│
├── terraform/           # Infrastructure as code (IMPORTANT: Independent directories)
│   ├── 2_sagemaker/     # SageMaker embedding endpoint
│   ├── 3_ingestion/     # S3 Vectors and ingestion Lambda
│   ├── 4_researcher/    # App Runner research service
│   ├── 5_database/      # Aurora Serverless v2
│   ├── 6_agents/        # Multi-agent Lambda functions
│   ├── 7_frontend/      # CloudFront, S3, API Gateway
│   └── 8_enterprise/    # Dashboards and CloudWatch monitoring
│
└── scripts/             # Deployment and local dev scripts
    ├── deploy.py        # Frontend deployment
    ├── run_local.py     # Local development
    └── destroy.py       # Cleanup script
```

---

## Course Structure: The 8 Guides

**IMPORTANT:** before working with the student, you MUST read all guides in the `guides` folder, in the correct order (1-8), to fully understand the project.

### Week 3: Research Infrastructure

**Day 3 - Fundamentals**
- **Guide 1: AWS Permissions** (1_permissions.md)
  - Configure IAM permissions for the Alex project
  - Create the AlexAccess group with required policies
  - Configure AWS CLI and credentials

- **Guide 2: SageMaker Deployment** (2_sagemaker.md)
  - Deploy a SageMaker serverless endpoint for embeddings
  - Use the HuggingFace model all-MiniLM-L6-v2
  - Test embedding generation
  - Understand serverless vs always-on endpoints

**Day 4 - Vector Storage**
- **Guide 3: Ingestion Pipeline** (3_ingest.md)
  - Create the S3 Vectors bucket (90% savings!)
  - Deploy the document ingestion Lambda function
  - Configure API Gateway with API key authentication
  - Test document storage and search

**Day 5 - Research Agent**
- **Guide 4: Research Agent** (4_researcher.md)
  - Deploy an autonomous research agent on App Runner
  - Use AWS Bedrock with the Nova Pro model
  - Integrate Playwright MCP server for web browsing
  - Configure an EventBridge scheduler (optional)
  - **IMPORTANT**: Update `backend/researcher/server.py` with your region and model

### Week 4: Portfolio Management Platform

**Day 1 - Database**
- **Guide 5: Database and Infrastructure** (5_database.md)
  - Deploy Aurora Serverless v2 PostgreSQL
  - Enable Data API (no VPC complexity!)
  - Create database schema
  - Load seed data (22 ETFs)
  - Configure shared database library

**Day 2 - Agent Orchestra**
- **Guide 6: AI Agent Orchestra** (6_agents.md)
  - Deploy 5 agent Lambdas (Planner, Tagger, Reporter, Charter, Retirement)
  - Configure SQS queue for orchestration
  - Configure collaboration patterns across agents
  - Test local and remote execution
  - Implement parallel agent processing

**Day 3 - Frontend**
- **Guide 7: Frontend and API** (7_frontend.md)
  - Configure Clerk authentication
  - Deploy NextJS frontend
  - Create FastAPI backend on Lambda
  - Configure CloudFront CDN
  - Test portfolio management and AI analysis

**Day 4 - Enterprise Features**
- **Guide 8: Enterprise Level** (8_enterprise.md)
  - Implement scalability settings
  - Add security layers (WAF, VPC endpoints, GuardDuty)
  - Configure CloudWatch dashboards and alarms
  - Implement guardrails and validations
  - Add explainability
  - Configure observability with LangFuse

As context, in previous weeks students learned how to deploy on AWS, key services like Lambda and App Runner, and Clerk for user management (requires NextJS with Pages Router).

---

## IMPORTANT: Working with students - approach

Students may be on Windows, Mac (Intel or Apple Silicon), or Linux. Always use uv for ALL Python code; there are uv projects in every directory. It is fine to have one uv project inside another, although uv may show a warning.

Always use `uv add package` and `uv run module.py`, but NEVER `pip install xxx`, NEVER `python -c "code"`, NEVER `python -m module.py`, and never `python script.py`.
It is VERY IMPORTANT not to use the python command outside a uv project.
Avoid shell scripts or Powershell scripts because they are platform-dependent. Strongly and consistently prefer Python scripts (via uv) and file handling through Cursor File Explorer, since this is clear for all students.

## Working with students: Core principles

### Before starting, always read all guides in the guides folder for full context

### 1. **Always establish context first**

When a student asks for help:
1. **Ask what guide/day they are on** - It is critical to know what infrastructure is already deployed
2. **Ask what they are trying to achieve** - Understand the goal before diving into code
3. **Ask what error or behavior they see** - Request the exact error message, not the student interpretation

### 2. **Diagnose before fixing** ⚠️ MOST IMPORTANT

**DO NOT jump into coding before understanding the real problem.**

Common mistakes to avoid:
- Writing defensive code with `isinstance()` checks without understanding root cause
- Adding try/except blocks that hide the real error
- Creating workarounds that mask the real issue
- Making many changes at once (makes debugging impossible)

**Instead, follow this process:**
1. **Reproduce the issue** - Ask for exact errors, logs, and commands used
2. **Identify root cause** - Use CloudWatch logs, AWS console, error traces
3. **Verify your understanding** - Explain what you think is happening and confirm with the student
4. **Propose the smallest possible change** - Change only one thing at a time
5. **Test and verify** - Confirm the fix works before moving on

### 3. **Common root causes (check these first)**

Before writing code, check these common problems:

**Docker Desktop is not running** (most common with `package_docker.py`)
- The script fails with a generic uv warning about nested projects
- The real issue is Docker not running
- Students get distracted by the uv warning (recently fixed in script)
- **Always ask**: Is Docker Desktop running?

**AWS permissions issues** (most common overall)
- Missing IAM policies for specific AWS services
- Region-specific permissions (especially Bedrock inference profiles)
- Inference profiles require permissions in MULTIPLE regions
- **Check**: IAM policies, AWS region settings, model access in Bedrock

**Terraform variables not configured**
- Every Terraform directory needs its `terraform.tfvars`
- Missing/incorrect variables cause hard-to-understand errors
- **Check**: Does `terraform.tfvars` exist? Are all required variables configured?

**AWS region mismatches**
- Bedrock models may only be available in specific regions
- Nova Pro requires inference profiles
- Cross-region access may require approved Bedrock models in multiple regions
- **Check**: Region consistency in config files

**Model access not granted**
- AWS Bedrock requires explicit model access requests
- Nova Pro is the recommended model (Claude Sonnet has strict limits)
- Access is region-based; inference profiles may require multiple regions
- **Check**: Bedrock console -> Model access

### 4. **Current model strategy**

**Use Nova Pro, not Claude Sonnet**
- Nova Pro (`us.amazon.nova-pro-v1:0` or `eu.amazon.nova-pro-v1:0`) is recommended
- Requires inference profiles for cross-region access
- Claude Sonnet limits are too strict for this project
- Students need to request access in Bedrock console (possibly in multiple regions)

### 5. **Testing strategy**

Each agent directory has two test files:
- `test_simple.py` - Local tests with mocks (use `MOCK_LAMBDAS=true`)
- `test_full.py` - AWS deployment tests (real Lambda invocations)

Students must:
1. Test locally with `test_simple.py`
2. Deploy with terraform/packaging
3. Test deployed system with `test_full.py`

### 6. **Help students help themselves**

Encourage students to:
- Read errors carefully (especially CloudWatch logs)
- Verify resources exist in AWS console
- Use `terraform output` to inspect details
- Test incrementally (do not deploy everything at once)
- Keep AWS costs in mind (remember to destroy resources when not actively working)

---

## Terraform Strategy

### Independent directory architecture

Each terraform directory (2_sagemaker, 3_ingestion, etc.) is **independent** and has:
- Its own local state file (`terraform.tfstate`)
- Its own `terraform.tfvars` configuration file
- No dependency on other terraform directories

**This is intentional** for learning purposes:
- Students can deploy step by step, guide by guide
- State files are local (simpler than remote/S3)
- Each part can be destroyed independently
- No state bucket or extra complexity is needed
- Infrastructure can be destroyed in stages

### Critical requirements

**⚠️ Students MUST configure `terraform.tfvars` in each directory before running terraform apply**

Typical flow is using Cursor File Explorer to copy `terraform.tfvars.example` to `terraform.tfvars` and adjust values in each directory.

If `terraform.tfvars` is missing or misconfigured:
- Terraform uses defaults (usually wrong)
- Resource creation may fail with confusing errors
- Service connections will fail

### Terraform state management

- State files are automatically `.gitignore`d
- Local state means no S3 bucket is needed
- Students can run `terraform destroy` independently in each directory
- If a student loses state, they may need to import existing resources or recreate

## Agent strategy - OpenAI Agents SDK context

Each Agent subdirectory has a common structure with idiomatic patterns.

1. `lambda_handler.py` for Lambda function and agent execution
2. `agent.py` for Agent creation and logic
3. `templates.py` for prompts

Alex uses OpenAI Agents SDK. Always use the newest and most idiomatic OpenAI Agents SDK APIs, recognizing the framework is new. When creating a new project, the correct package is `openai-agents`, not `agents`. So if you create a new project, use `uv add openai-agents` and then `from agents import Agent, Runner, trace` in code.

Alex uses LiteLLM to connect to Bedrock:

`model = LitellmModel(model=f"bedrock/{model_id}")`

Structured outputs and tool calling are used often, but due to a current LiteLLM/Bedrock limitation, the same Agent cannot use both (structured outputs and tools) at once. So each Agent implementation uses one or the other, never both.

This is the standard idiomatic approach in `lambda_handler`:

```python
    # Create agent - imported from agents.py
    model, tools, task = create_agent(job_id, portfolio_data, user_preferences, db)
    
    # Run agent
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

In cases where a Tool needs to know which user is logged in to query the database correctly, we use a standard idiomatic approach to pass context to the Tool. It works very well and is recommended by OpenAI Agents SDK.

```python

with trace("Reporter Agent"):
        agent = Agent[ReporterContext](  # Specify context type
            name="Report Writer", instructions=REPORTER_INSTRUCTIONS, model=model, tools=tools
        )

        result = await Runner.run(
            agent,
            input=task,
            context=context,  # Pass context
            max_turns=10,
        )

        response = result.final_output

```
And later:
```python
@function_tool
async def get_market_insights(
    wrapper: RunContextWrapper[ReporterContext], symbols: List[str]
) -> str:
...
```

IMPORTANT: when using Bedrock through LiteLLM, LiteLLM needs this environment variable defined:  
`os.environ["AWS_REGION_NAME"] = bedrock_region`  
This can be confusing because other services may expect `"AWS_REGION"` or `"DEFAULT_AWS_REGION"`. But LiteLLM needs `AWS_REGION_NAME` exactly as documented here: https://docs.litellm.ai/docs/providers/bedrock.


---

## Common issues and troubleshooting

The most common issues are related to AWS region selection. Check environment variables and terraform settings (everything should flow from tfvars)!

### Problem 1: `package_docker.py` failure

**Symptoms**: Script fails with uv warning about nested projects and maybe an error message

**Common root cause**: Docker Desktop is not running or "Docker mounts denied"

**Diagnosis**:
1. Ask: Is Docker Desktop running?
2. Check: Can `docker ps` run successfully?
3. Recent fix: Script now shows better messages, but older versions were confusing

**Solution**: Start Docker Desktop, wait for full initialization, and retry

**If issue is Mounts Denied**: It cannot mount `/tmp` because Docker has no access. Open Docker Desktop and add the mentioned directory to File Sharing (Settings -> Resources -> File Sharing), this solved it for one student.

**NOT a solution**: Changing uv project settings (this is a false lead)

### Problem 2: Region issues and Bedrock model access

**Symptoms**: "Access denied" or "Model not found" errors when running agents

**Root cause**: Model access not granted in Bedrock or wrong region

**Diagnosis**:
1. Which model are they trying to use?
2. What region is code running in?
3. Did they request model access in Bedrock console?
4. For inference profiles: do they have permissions in multiple regions?
5. Are env vars set correctly? LiteLLM needs `AWS_REGION_NAME`. Ensure nothing is hardcoded in code and tfvars are correct. Add logs to confirm effective region.

**Solution**:
1. Go to Bedrock console in the correct region
2. Click "Model access"
3. Request access to Nova Pro
4. For cross-region access: configure inference profiles with multi-region permissions

### Problem 3: Terraform Apply failure

**Symptoms**: Resources not created, dependency errors, ARN not found

**Root cause**: `terraform.tfvars` not configured, or values from previous guides not copied

**Diagnosis**:
1. Does `terraform.tfvars` exist in this directory?
2. Are all required variables present (see `terraform.tfvars.example`)?
3. In later guides: do they have outputs from previous guides?
4. Run `terraform output` in previous directories to get required ARNs

**Solution**:
1. Copy `terraform.tfvars.example` to `terraform.tfvars`
2. Fill all required values
3. Get ARNs from previous outputs: `cd terraform/X_previous && terraform output`
4. Update `.env` with new values for Python scripts

### Problem 4: Lambda function failures

**Symptoms**: 500 errors, timeouts, "Module not found"

**Root cause**: Bad packaging, missing environment variables, IAM permissions

**Diagnosis**:
1. Check CloudWatch logs: `aws logs tail /aws/lambda/alex-{agent-name} --follow`
2. Check lambda environment variables in AWS console
3. Verify IAM role has required permissions
4. Was Lambda package built with Docker for linux/amd64?

**Solution**:
1. Packaging: rerun `package_docker.py` with Docker running
2. Env vars: verify in Lambda console or `terraform.tfvars`
3. Permissions: review IAM role policy in terraform

### Problem 5: Aurora database connection error

**Symptoms**: "Cluster not found", "Secret not found", Data API errors

**Root cause**: Database not initialized, wrong ARNs, or Data API disabled

**Diagnosis**:
1. Check cluster status: `aws rds describe-db-clusters`
2. Verify Data API is enabled (must show `EnableHttpEndpoint: true`)
3. Verify ARNs in environment variables match real resources
4. DB initialization may take time (10-15 minutes)

**Solution**:
1. Wait until cluster is in "available" state
2. Verify Data API is enabled in RDS console
3. Run `terraform output` in `5_database` to get real ARNs
4. Update environment variables with correct ARNs

---

## Quick technical architecture reference

### Main services by guide

**Guides 1-2**: Fundamentals
- IAM permissions
- SageMaker serverless endpoint (embeddings)

**Guide 3**: Vector storage
- S3 Vectors bucket and index
- Ingestion Lambda function
- API Gateway with API key

**Guide 4**: Research agent
- App Runner service (Researcher)
- ECR repository
- EventBridge scheduler (optional)

**Guide 5**: Database
- Aurora Serverless v2 PostgreSQL
- Data API enabled
- Secrets Manager for credentials
- Schema and seed data - **IMPORTANT** review schema

**Guide 6**: Agent Orchestra (the key one)
- 5 Lambda functions: Planner, Tagger, Reporter, Charter, Retirement
- Each lambda implemented with simple idiomatic code using OpenAI Agents SDK. Review an existing implementation.
- SQS queue for orchestration
- S3 bucket for Lambda packages (>50MB)
- Inter-service IAM permissions

**Guide 7**: Frontend
- Static NextJS site on S3
- CloudFront CDN
- API Gateway + Lambda backend
- Clerk authentication

**Guide 8**: Enterprise
- CloudWatch dashboards
- Alarms and monitoring
- LangFuse observability
- Advanced logging

### Agent collaboration pattern

```
User request -> SQS Queue -> Planner (Orchestrator)
                            |- -> Tagger (if needed)
                            |- -> Reporter --|
                            |- -> Charter ---|-> Results -> Database
                            \- -> Retirement -|
```

### Cost management

**Cost optimization:**
- Destroy Aurora when you are not actively working (largest savings)
- Use `terraform destroy` in each directory
- Monitor costs in AWS Cost Explorer

### Cleanup process

```bash
# Destroy in reverse order (optional, but cleaner)
cd terraform/8_enterprise && terraform destroy
cd terraform/7_frontend && terraform destroy
cd terraform/6_agents && terraform destroy
cd terraform/5_database && terraform destroy  # Maximum cost savings
cd terraform/4_researcher && terraform destroy
cd terraform/3_ingestion && terraform destroy
cd terraform/2_sagemaker && terraform destroy
```

---

## Key files students modify

### Configuration files
- `.env` - Root environment variables (add values as you progress through guides)
- `frontend/.env.local` - Clerk frontend configuration
- `terraform/*/terraform.tfvars` - Each terraform dir (copy from .example)

### Code students can edit
- `backend/researcher/server.py` - Region and model configuration (Guide 4) - but this should come from variables and not require code changes
- Agent templates in `backend/*/templates.py` - For customization
- Frontend pages for UI changes

---

## How to get help

### For students

If you are stuck:

1. **Review the guide carefully** - Almost all steps include troubleshooting sections
2. **Look at error messages** - Read CloudWatch logs, not only terminal output
3. **Verify prerequisites** - Is Docker running? Are permissions ready? Is terraform.tfvars configured?
4. **Contact the instructor**:
   - **Post a question in Frogames Formacion** - Include guide number, exact error, and what you tried
   - **Email Juan Gabriel Gomila**: juangabriel@frogames.es

When asking for help, include:
- Which guide/day you are on
- Exact error message (copy/paste, do not paraphrase)
- Which command you ran
- Relevant CloudWatch logs if possible
- What you already tried

### For Claude Code (AI Assistant)

When helping students:

0. **Prepare** - Read all guides to be fully informed
1. **Set context** - Which guide? What is the objective?
2. **Request error details** - Real messages, logs, console output
3. **Diagnose first** - Do not write code before understanding the issue
4. **Go step by step** - Incremental changes
5. **Verify your understanding** - Explain what you think is happening before fixing
6. **Keep it simple** - Avoid over-engineered solutions

**Remember**: Students are learning. The goal is to help them understand WHAT went wrong and how to fix it, not only make the error disappear.

---

### Course context
- Instructor: Juan Gabriel Gomila
- Platform: Frogames Formacion
- Course: AI in Production
- Project: "Alex" - Capstone project weeks 3-4

---

*This guide was created to help AI assistants (like Claude Code) effectively support students on the Alex project. Last update: October 2025*
