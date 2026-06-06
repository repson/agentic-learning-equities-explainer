# Alex - Project Guide for the "AI in Production" Course

## Project Overview

**Alex** (Agentic Learning Equities eXplainer) is a multi-agent based enterprise SaaS financial planning platform. This is the final project for Weeks 3 and 4 of the "AI in Production" course taught by Juan Gabriel Gomila at Frogames Formación, in which agent solutions are deployed in production.

The user is a student of the course. You are collaborating with the user to help them build Alex successfully. The user works on Cursor (the fork of VS Code), and could be on a Windows PC, a Mac (intel or Apple silicon), or a Linux machine. All python code runs with uv and there are uv projects in every directory that requires it. The student is familiar with AWS services (Lambda, App Runner, Cloudfront) and has been introduced to Terraform, uv, NextJS and docker. They have budget alerts set up, but should periodically review the billing screens in the AWS console to keep an eye on costs.

The student has an AWS root user and also an IAM user named "aiengineer" with permissions. They have run `aws configure` and should be logged in as "aiengineer" with their default region.

### What will students build?

Students will deploy a complete production AI system that includes:
- **Multi-agent collaboration**: 5 specialized AI agents working together through orchestration
- **Serverless architecture**: Lambda, Aurora Serverless v2, App Runner, API Gateway, SQS
- **Cost-optimized vector storage**: S3 Vectors (90% cheaper than OpenSearch!)
- **Real-time financial analysis**: Portfolio management, retirement projections, market research
- **Production grade practices**: Observability, protections, security, monitoring
- **Full-stack application**: NextJS React Frontend with Clerk authentication

### Learning Objectives

Upon completing this project, students will:
1. They will deploy and manage production AI infrastructure on AWS
2. They will implement multi-agent systems using the OpenAI Agents SDK
3. They will integrate AWS Bedrock (with the Nova Pro model) for LLM capabilities
4. They will build cost-effective vector search with S3 Vectors and SageMaker embeddings
5. They will create serverless orchestration of agents with SQS and Lambda
6. They will deploy a complete full-stack SaaS application
7. They will implement enterprise features: monitoring, observability, protections, security

### Commercial Product

Alex is a SaaS product that provides information about users' stock portfolios through reports and graphs. Alex is integrated with Clerk for user management and the database architecture keeps each user's data separate.

---

## Directory Structure

```
alex/
├── guides/ # Step-by-step deployment guides (START HERE)
│ ├── 1_permissions.md
│ ├── 2_sagemaker.md
│ ├── 3_ingest.md
│ ├── 4_researcher.md
│ ├── 5_database.md
│ ├── 6_agents.md
│   ├── 7_frontend.md
│ ├── 8_enterprise.md
│ ├── architecture.md
│ └── agent_architecture.md
│
├── backend/ # Code for agents and Lambda functions
│ ├── planner/ # Orchestrating agent
│ ├── tagger/ # Instrument classification agent
│ ├── reporter/ # Portfolio analysis agent
│ ├── charter/ # Display agent
│ ├── retirement/ # Retirement projection agent
│ ├── researcher/ # Market research agent (App Runner)
│ ├── ingest/ # Document ingestion Lambda
│ ├── database/ # Shared database library
│ └── api/ # Backend FastAPI for the frontend
│
├── frontend/ # NextJS React application
│ ├── pages/
│ ├── components/
│ └── lib/
│
├── terraform/ # Infrastructure as code (IMPORTANT: Independent directories)
│ ├── 2_sagemaker/ # Endpoint embeddings SageMaker
│ ├── 3_ingestion/ # S3 Vectors and Lambda ingestion
│ ├── 4_researcher/ # Research App Runner Service
│ ├── 5_database/ # Aurora Serverless v2
│ ├── 6_agents/ # Multi-agent Lambda functions
│ ├── 7_frontend/ # CloudFront, S3, API Gateway
│ └── 8_enterprise/ # CloudWatch Dashboards and Monitoring
│
└── scripts/ # Local development and deployment scripts
    ├── deploy.py # Frontend deployment
    ├── run_local.py # Local development
    └── destroy.py # Cleanup script
```

---

## Course Structure: The 8 Guides

**IMPORTANT:** Before working with the student, you MUST read all the guides in the guides folder, in the correct order (1-8), to fully understand the project.

### Week 3: Research Infrastructure

**Day 3 - Fundamentals**
- **Guide 1: AWS Permissions** (1_permissions.md)
  - Configure IAM permissions for the Alex project
  - Create the AlexAccess group with the required policies
  - Configure AWS CLI and credentials

- **Guide 2: Deploying SageMaker** (2_sagemaker.md)
  - Deploy SageMaker Serverless endpoint for embeddings
  - Use the HuggingFace all-MiniLM-L6-v2 model
  - Test the generation of embeddings
  - Understand serverless vs always-on endpoints

**Day 4 - Vector Storage**
- **Guide 3: Ingestion Pipeline** (3_ingest.md)
  - Create S3 Vectors bucket (90% savings!)
  - Deploys Lambda function for document ingestion
  - Configure API Gateway with API key authentication
  - Test document storage and search

**Day 5 - Investigative Agent**
- **Guide 4: Investigative Agent** (4_researcher.md)
  - Deploy autonomous investigative agent in App Runner
  - Use AWS Bedrock with Nova Pro model
  - Integrates Playwright MCP server for web browsing
  - Configure EventBridge scheduler (optional)
  - **IMPORTANT**: Update `backend/researcher/server.py` with your region and model

### Week 4: Portfolio Management Platform

**Day 1 - Database**
- **Guide 5: Database and Infrastructure** (5_database.md)
  - Deploys Aurora Serverless v2 PostgreSQL
  - Enable Data API (no VPC complexities!)
  - Create the database schema
  - Load example data (22 ETFs)
  - Configure the shared database library

**Day 2 - Agents Orchestra**
- **Guide 6: IA Agent Orchestration** (6_agents.md)
  - Deploy 5 Lambda agents (Planner, Tagger, Reporter, Charter, Retirement)
  - Configure SQS queue for orchestration
  - Configure collaboration patterns between agents
  - Test local and remote execution
  - Implements parallel processing of agents

**Day 3 - Frontend**
- **Guide 7: Frontend and API** (7_frontend.md)
  - Configure Clerk authentication
  - Deploy NextJS React frontend
  - Create FastAPI backend in Lambda
  - Configure CDN CloudFront
  - Try portfolio management and AI analysis

**Day 4 - Business Features**
- **Guide 8: Business Degree** (8_enterprise.md)
  - Implement scalability configurations
  - Add security layers (WAF, VPC endpoints, GuardDuty)
  - Configure CloudWatch dashboards and alarms
  - Implement protections and validation
  - Add explainability features
  - Configure observability with LangFuse

For context, in previous weeks the students learned how to deploy the main AWS services such as Lambda and App Runner in AWS, and the use of Clerk for user management (requires NextJS with Pages Router).

---

## IMPORTANT: How to work with students - approach

Students can be on Windows PC, Mac (Intel or Apple Silicon), or Linux. Always use uv for ALL python code; there are uv projects in each directory. There is no problem with having one uv project inside another, although uv may display a warning.

Always do `uv add package` and `uv run module.py`, but NEVER `pip install xxx` and NEVER `python -c "code"` or `python -m module.py` or `python script.py`.
It is VERY IMPORTANT not to use the python command outside of a uv project.
Avoid shell or Powershell scripts as they are platform dependent. He prefers to write python scripts (via uv) and manage files in the Cursor File Explorer, as this is clearer for all students.

## Working with Students: Fundamental Principles

### Before starting, always read all the guides in the guides folder to have all the context

### 1. **First Establish the Context**

When a student requests help:
1. **Ask what guide/day they are on** - This is critical to know what infrastructure they have deployed
2. **Ask what they are trying to achieve** - Understand the goal before getting into the code
3. **Ask what error or behavior they see** - Ask for the actual error message, not an interpretation

### 2. **Diagnose Before Fixing** ⚠️ THE MOST IMPORTANT THING

**DO NOT jump to conclusions or write a lot of code before fully understanding the problem.**

Common mistakes to avoid:
- Writing defensive code with `isinstance()` checks without understanding the root cause
- Add try/except blocks that hide the real error
- Create solutions that only mask the real problem
- Make multiple changes at once (complicates debugging)

**Instead, follow this process:**
1. **Reproduce the problem** - Ask for exact error messages, logs, commands
2. **Identify the root cause** - Use CloudWatch logs, the AWS console, error traces
3. **Check your understanding** - Explain what you think is happening and confirm with the student
4. **Propose the minimum change** - One change at a time
5. **Test and verify** - Confirm that the solution works before continuing

### 3. **Common Root Causes (Check These First)**

Before writing code, review these common problems:

**Docker Desktop is not active** (Very common with `package_docker.py`)
- Script will fail with generic uv warning on nested projects
- The real problem is that Docker is not running
- Students are often distracted by the uv warning (this was recently fixed in the script)
- **Always ask**: "Is Docker Desktop running?"

**Permissions problems in AWS** (The most common in general)
- Missing IAM policies for certain AWS services
- Region-specific permissions (especially for inference profiles in Bedrock)
- Inference profiles require permissions for MULTIPLE regions
- **Review**: IAM policies, region configuration in AWS, access to Bedrock models

**Terraform variables not configured**
- Each terraform directory needs its `terraform.tfvars` file configured
- Missing or incorrect variables cause cryptic errors
- **Check**: Does `terraform.tfvars` exist? Are all the required variables?

**Region mismatches in AWS**
- Bedrock models may only be available in certain regions
- Nova Pro requires inference profiles
- Cross-region access may require approval of models in Bedrock in multiple regions
- **Check**: Region consistency in configuration files

**Access to model not granted**
- AWS Bedrock requires explicit model access requests
- Nova Pro is the recommended model (Claude Sonnet has very strict limits)
- Access is by region; inference profiles may require multiple approved regions
- **Check**: Bedrock Console → Access to models

### 4. **Current Model Strategy**

**Use Nova Pro, not Claude Sonnet**
- Nova Pro (`us.amazon.nova-pro-v1:0` or `eu.amazon.nova-pro-v1:0`) is the recommended model
- Requires inference profiles for cross-region access
- Claude Sonnet has too strict limits for this project
- Students must request access in the AWS Bedrock console, perhaps in multiple regions

### 5. **Testing Approach**

Each agent directory has two test files:
- `test_simple.py` - Local test with mocks (use `MOCK_LAMBDAS=true`)
- `test_full.py` - Test AWS deployment (actual Lambda invocations)

Students must:
1. Test first locally with `test_simple.py`
2. Deploy with terraform/packaging
3. Test the deployment with `test_full.py`

### 6. **Help students help themselves**

Encourage students to:
- Read error messages carefully (especially logs in CloudWatch)
- Verify in the AWS console that the resources exist
- Use `terraform output` to see details of deployed resources
- Test incrementally (don't deploy everything at once)
- Keep AWS costs in mind (remember to destroy when not working)

---

## Terraform Strategy

### Independent Directory Architecture

Each terraform directory (2_sagemaker, 3_ingestion, etc.) is **independent** with:
- Your own local state file (`terraform.tfstate`)
- Your own `terraform.tfvars` configuration
- No dependencies between terraform directories

**This is intentional** for educational reasons:
- Students can unfold little by little, guide by guide
- State files are local (simpler than using remote S3)
- Each part can be destroyed separately
- No need to configure complex state bucket
- You can destroy the infrastructure step by step

### Critical Requirements

**⚠️ Students MUST set `terraform.tfvars` in each directory before running terraform apply**

The typical pattern is to use Cursor File Explorer to copy terraform.tfvars.example to terraform.tfvars and then modify the variables in each directory.

If `terraform.tfvars` is missing or misconfigured:
- Terraform will use default values ​​(often wrong)
- Resources may fail to create with cryptic errors
- Connections between services will be broken

### Terraform State Management

- State files are automatically in `.gitignore`
- Local state means no S3 bucket needed
- Students can run `terraform destroy` on each directory independently
- If a student loses status, you may need to import existing resources or recreate them

## Agent strategy - background on OpenAI Agents SDK

Each Agent subdirectory has a common structure and language patterns.

1. `lambda_handler.py` for lambda function and agent execution
2. `agent.py` for creating Agent and its code
3. `templates.py` for prompts

Alex uses the OpenAI Agents SDK. Make sure to always use the latest OpenAI Agents SDK language APIs, recognizing that it is a new framework. Although it is already installed in all uv projects, remember that the correct package name is `openai-agents` and not `agents`. So if you ever create a new project, you'll need to do `uv add openai-agents` followed by this import in the `from agents import Agent, Runner, trace` code.

Alex uses standard LiteLLM to connect to Bedrock:

`model = LitellmModel(model=f"bedrock/{model_id}")`

Structured output and Tool calling are frequently used, but due to a limitation of LiteLLM with Bedrock, the same Agent cannot use both at the same time. Thus, every Agent implementation uses structured output *OR* tools, never both.

This is the standard idiomatic approach used in lambda_handler:

```python
    # Create agent - imported from agents.py
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

In cases where a Tool needs to know which user is authenticated to make the correct DB call, we use a standard, idiomatic context passing approach that works very well and is recommended by the OpenAI Agents SDK.

```python

with trace("Reporter Agent"):
        agent = Agent[ReporterContext]( # Specifies the type of context
            name="Report Writer", instructions=REPORTER_INSTRUCTIONS, model=model, tools=tools
        )

        result = await Runner.run(
            agent,
            input=task,
            context=context, # Pass the context
            max_turns=10,
        )

        response = result.final_output

```
And then:
```python
@function_tool
async def get_market_insights(
    wrapper: RunContextWrapper[ReporterContext], symbols: List[str]
) -> str:
...
```

IMPORTANT: When using Bedrock using LiteLLM, LiteLLM requires this environment variable to be set:
`os.environ["AWS_REGION_NAME"] = bedrock_region`
This can be confusing since other services expect `"AWS_REGION"` or `"DEFAULT_AWS_REGION"`. But LiteLLM needs `AWS_REGION_NAME` as documented here: https://docs.litellm.ai/docs/providers/bedrock.


---

## Common Problems and Error Resolutions

The most common problems are related to the choice of AWS region! Check environment variables, terraform configuration (everything should be propagated from tfvars).

### Problema 1: `package_docker.py` falla

**Symptoms**: Script fails with uv warning on nested projects and perhaps an error message

**Root Cause (Common)**: Docker Desktop not running or Docker mount denied error

**Diagnosis**:
1. Question: "Is Docker Desktop running?"
2. Check: Can they run `docker ps` correctly?
3. Recent update: The script now gives better errors, but old versions were confusing

**Solution**: Start Docker Desktop, wait for it to fully initialize and try again

**If the error is Mounts Denied**: Fails to mount the /tmp directory in Docker because it does not have permissions. Going to the Docker Desktop app and adding the mentioned directory to File Sharing (Settings -> Resources -> File Sharing) solved it for one student.

**Not the solution**: Change uv project settings (this is a red herring)

### Issue 2: Region Issues and Access Denied to Bedrock Model

**Symptoms**: "Access denied" or "Model not found" errors when running agents

**Root Cause**: Model access not granted in Bedrock, or incorrect region

**Diagnosis**:
1. What model are you trying to use?
2. What region does your code run in?
3. Have you requested access to the model in the Bedrock console?
4. For inference profiles: Do you have permissions in multiple regions?
5. Are the environment variables set correctly? LiteLLM requires `AWS_REGION_NAME`. Check that nothing is hardcoded in the code, and that the tfvars are correct. Add logs to confirm the region used.

**Solution**:
1. Go to the Bedrock console in the correct region
2. Click on "Model access"
3. Request access to Nova Pro
4. For cross-region use: Configure inference profiles with multi-region permissions

### Problema 3: Falla terraform apply

**Symptoms**: Resources fail to create, dependency errors, ARN not found

**Root Cause**: `terraform.tfvars` not configured or missing previous guide values

**Diagnosis**:
1. Does `terraform.tfvars` exist in this directory?
2. Are all the required variables present? (check `terraform.tfvars.example`)
3. For subsequent guides: Do you have the outputs of previous guides?
4. Run `terraform output` on previous directories to obtain the necessary ARNs

**Solution**:
1. Copy `terraform.tfvars.example` to `terraform.tfvars`
2. Fill in all required values
3. Get ARNs from previous outputs: `cd terraform/X_previous && terraform output`
4. Update the `.env` file with the correct values ​​for python scripts

### Problem 4: Lambda failures

**Symptoms**: 500 errors, timeouts, "Module not found" in Lambda

**Root Cause**: Package not built correctly, missing environment variables, or missing IAM permissions

**Diagnosis**:
1. Check CloudWatch logs: `aws logs tail /aws/lambda/alex-{agent-name} --follow`
2. Check environment variables in the Lambda console
3. Verify that the IAM role has required permissions
4. Was the Lambda package built with Docker for linux/amd64?

**Solution**:
1. For packaging: Run `package_docker.py` again with Docker running
2. For env vars: Check in the Lambda console or `terraform.tfvars`
3. For permissions: Review the IAM policy in terraform

### Problem 5: Connection to Aurora base fails

**Symptoms**: "Cluster not found", "Secret not found", Data API errors

**Root Cause**: Database not initialized, incorrect ARNs, or Data API not enabled

**Diagnosis**:
1. Check cluster status: `aws rds describe-db-clusters`
2. Verify that Data API is enabled (`EnableHttpEndpoint: true`)
3. Check that the ARNs in the environment variables match the resources
4. It may be in the process of initialization (takes 10-15 minutes)

**Solution**:
1. Wait for the cluster to be in the "available" state
2. Check Data API in RDS console
3. Run `terraform output` on `5_database` to get correct ARNs
4. Update the environment variables with the real ARNs

---

## Technical Architecture Quick Reference

### Main services per guide

**Guides 1-2**: Fundamentals
- IAM permissions
- SageMaker Serverless Endpoint (embeddings)

**Guide 3**: Vector Storage
- Bucket S3 Vectors and index
- Ingestion Lambda
- API Gateway with API key

**Guide 4**: Investigative Agent
- App Runner Service (Researcher)
- ECR Repository
- EventBridge scheduler (optional)

**Guide 5**: Database
- Aurora Serverless v2 PostgreSQL
- Data API enabled
- Secrets Manager for credentials
- Scheme and seed data - **IMPORTANT** read the DB scheme

**Guide 6**: Agents Orchestra (The Great Guide)
- 5 Lambda functions: Planner, Tagger, Reporter, Charter, Retirement
- Each Lambda implemented using OpenAI Agents SDK with simple and idiomatic code. Review an existing implementation for details.
- SQS queue for orchestration
- S3 bucket for Lambda packets (>50MB)
- Cross IAM permissions

**Guide 7**: Frontend
- NextJS static site on S3
- CDN CloudFront
- API Gateway + Lambda backend
- Clerk Authentication

**Guide 8**: Business
- CloudWatch Dashboards
- Alarms and monitoring
- LangFuse Observability
- Advanced logging

### Agent Collaboration Pattern

```
User Request → SQS Queue → Planner
                            ├─→ Tagger (if needed)
                            ├─→ Reporter ──┐
                            ├─→ Charter ───┼─→ Results → BD
                            └─→ Retirement ┘
```

### Cost Management

**Cost optimization**:
- Destroy Aurora when you are not actively working (greater savings)
- Use `terraform destroy` on each directory
- Monitor costs in AWS Cost Explorer

### Cleaning process

```bash
# Destroy in reverse order (optional, but cleaner)
cd terraform/8_enterprise && terraform destroy
cd terraform/7_frontend && terraform destroy
cd terraform/6_agents && terraform destroy
cd terraform/5_database && terraform destroy # Big cost savings
cd terraform/4_researcher && terraform destroy
cd terraform/3_ingestion && terraform destroy
cd terraform/2_sagemaker && terraform destroy
```

---

## Key Files that Students Modify

### Configuration Files
- `.env` - Root environment variables (add values ​​according to each guide)
- `frontend/.env.local` - Frontend Clerk configuration
- `terraform/*/terraform.tfvars` - Each terraform directory (copy from .example)

### Code that students may need to modify
- `backend/researcher/server.py` - Region and model configuration (Guide 4) - but this should come from variables and not require code changes
- Agent templates in `backend/*/templates.py` - For customization
- Frontend pages for UI modifications

---

## Obtener Ayuda

### For Students

If you got stuck:

1. **Review the guide carefully** - Most steps have a troubleshooting section
2. **Read error messages** - Look at the logs in CloudWatch, not just the terminal
3. **Check prerequisites** - Is Docker running? Are the permissions set? Has terraform.tfvars been configured?
4. **Contact the instructor**:
   - **Ask a question on Frogames** - Include tracking number, error message and what you tried
   - **Email Juan Gabriel**: juangabriel@frogames.es

When you ask for help, include:
- What guide/day are you on?
- Exact error message (copy/paste, do not summarize)
- What command did you execute?
- Relevant CloudWatch logs if you have
- What have you tried so far?

### For Claude Code (AI Assistant)

When helping students:

0. **Be Prepared** - Read all the guides to put yourself in context.
1. **Set the context** - What guide? What is the objective?
2. **Get error details** - Actual messages, logs, console
3. **Diagnose first** - Don't write code without understanding the problem
4. **Think incrementally** - One change at a time
5. **Check your understanding** - Explain what you think is happening before fixing
6. **Keep it simple** - Avoid over-engineering

**Remember**: Students are learning. The goal is to help them understand what happened and how to fix it, not just eliminate the error.

---

### Course Context
- Instructor: Juan Gabriel Gomila
- Platform: Frogames Training
- Course: AI in Production
- Project: "Alex" - Final project Weeks 3-4

---

*This guide was created to help AI assistants (like Claude Code) effectively support students with the Alex project. Last update: October 2025*
