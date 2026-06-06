# Alex - "AI in Production" Course Project Guide

## Project Summary

**Alex** (Agentic Learning Equities eXplainer) is a multi-agent based enterprise financial planning SaaS platform. It is the final project of weeks 3 and 4 of the "AI in Production" course taught by Juan Gabriel Gomila at Frogames Formación, which brings agent solutions to production.

The user is a student of the course. You work with the user to help them build Alex successfully. The student uses Cursor (the fork of VS Code) and can be on a Windows PC, a Mac (Intel or Apple silicon), or a Linux machine. All Python code runs with uv and there are uv projects in every directory that requires it. The student is familiar with AWS services (Lambda, App Runner, Cloudfront) and has been introduced to Terraform, uv, NextJS and Docker. They have budget alerts set up, but they should frequently review the billing screens in the AWS console to keep an eye on costs.

The student has an AWS root user and also an IAM user called "aiengineer" with permissions. They have run `aws configure` and should be logged in as the aiengineer user with their default region.

### What Students Will Build

Students will deploy a complete AI system in production that includes:
- **Multi-agent collaboration**: 5 specialized AI agents working together through orchestration
- **Serverless architecture**: Lambda, Aurora Serverless v2, App Runner, API Gateway, SQS
- **Cost-optimized vector storage**: S3 Vectors (90% cheaper than OpenSearch!)
- **Real-time financial analysis**: Portfolio management, retirement projections, market research
- **Production level practices**: Observability, guardrails, security, monitoring
- **Full-stack application**: React NextJS Frontend with Clerk authentication

### Learning Objectives

Upon completing this project, students will:
1. They will deploy and manage AI infrastructure in production on AWS
2. They will implement multi-agent systems using the OpenAI Agents SDK
3. They will integrate AWS Bedrock (with the Nova Pro model) for LLM capabilities
4. Build optimized vector search using S3 Vectors and SageMaker embeddings
5. They will create serverless orchestration of agents with SQS and Lambda
6. They will deploy a complete full-stack SaaS application
7. They will implement business functionalities: monitoring, observability, guardrails, security

### Commercial Product

Alex is a SaaS product that provides insights into users' equity portfolios through reports and charts. Alex is integrated with Clerk for user management and the database architecture keeps user data separate.

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
├── frontend/ # React NextJS application
│ ├── pages/
│ ├── components/
│ └── lib/
│
├── terraform/ # Infrastructure as code (IMPORTANT: independent directories)
│ ├── 2_sagemaker/ # Endpoint embedding SageMaker
│ ├── 3_ingestion/ # S3 Vectors and Ingestion Lambda
│ ├── 4_researcher/ # Research App Runner Service
│ ├── 5_database/ # Aurora Serverless v2
│ ├── 6_agents/ # multi-agent Lambdas
│ ├── 7_frontend/ # CloudFront, S3, API Gateway
│ └── 8_enterprise/ # Dashboards and CloudWatch monitoring
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
  - Create AlexAccess group with the necessary policies
  - Configure AWS CLI and credentials

- **Guide 2: Deploying SageMaker** (2_sagemaker.md)
  - Deploy SageMaker serverless endpoint for embeddings
  - Use HuggingFace model all-MiniLM-L6-v2
  - Test the generation of embeddings
  - Understand serverless vs always-on endpoints

**Day 4 - Vector Storage**
- **Guide 3: Intake Pipeline** (3_ingest.md)
  - Create S3 Vectors bucket (90% cost savings!)
  - Deploy Lambda document ingestion
  - Configure API Gateway with API key authentication
  - Test document storage and search

**Day 5 - Investigation Agent**
- **Guide 4: Investigative Agent** (4_researcher.md)
  - Deploy the autonomous research agent in App Runner
  - Use AWS Bedrock with Nova Pro model
  - Integrate Playwright MCP server for web browsing
  - Configure EventBridge scheduler (optional)
  - **IMPORTANT**: Update `backend/researcher/server.py` with your region and model

### Week 4: Portfolio Management Platform

**Day 1 - Database**
- **Guide 5: Database and Infrastructure** (5_database.md)
  - Deploy Aurora Serverless v2 PostgreSQL
  - Enable Data API (no VPC complexity!)
  - Create database schema
  - Load example data (22 ETFs)
  - Configure shared database library

**Day 2 - Agents Orchestra**
- **Guide 6: IA Agent Orchestra** (6_agents.md)
  - Deploy 5 agent lambdas (Planner, Tagger, Reporter, Charter, Retirement)
  - Configure SQS queue for orchestration
  - Define collaboration patterns between agents
  - Test local and remote execution
  - Implement parallel processing of agents

**Day 3 - Frontend**
- **Guide 7: Frontend and API** (7_frontend.md)
  - Set up Clerk authentication
  - Deploy React NextJS frontend
  - Create FastAPI backend on Lambda
  - Configure CloudFront CDN
  - Try portfolio management and AI analysis

**Day 4 - Business Features**
- **Guide 8: Enterprise Level** (8_enterprise.md)
  - Implement scalability configuration
  - Add security (WAF, VPC endpoints, GuardDuty)
  - Configure dashboards and alarms in CloudWatch
  - Implement guardrails and validation
  - Add explainability
  - Configure observability with LangFuse

As context, in previous weeks students learned how to deploy key services such as Lambda and App Runner on AWS, and how to use Clerk for user management (requires NextJS with Pages Router).

---

## IMPORTANT: How to Work with Students

Students can be on Windows, Mac (Intel or Apple Silicon), or Linux. Always use uv for ALL Python code; there are uv projects in each directory. There is no problem with having one uv project inside another, although uv may display a warning.

Always do `uv add package` and `uv run module.py`, but NEVER `pip install xxx` and NEVER `python -c "code"` or `python -m module.py` or `python script.py`.
It is VERY IMPORTANT not to use the python command outside of a uv project.
Avoid shell scripts or Powershell scripts as they are system dependent. Prioritize writing scripts in Python (via uv) and managing files in the Cursor File Explorer, as this will be clear to all students.

## Basic Principles When Helping Students

### Before starting, always read all the guides in the guides folder to have all the context

### 1. **Always Set Context First**

When a student asks for help:
1. **Ask what guide/day it is on** - It is critical to know what infrastructure you have deployed
2. **Ask what you are trying to achieve** - Before looking at the code, understand the goal
3. **Ask what error or behavior you see** - Ask for the actual error, not just the interpretation

### 2. **Diagnose Before Fixing** ⚠️ THE MOST IMPORTANT THING

**DO NOT jump to conclusions or write a lot of code before you understand the problem.**

Common mistakes:
- Writing defensive code with `isinstance()` checks without understanding the actual source
- Add try/except that hide the real error
- Create alternative solutions that cover up the real problem
- Make multiple changes at once (makes debugging difficult)

**Instead, follow this process:**
1. **Reproduce the problem** - Ask for exact errors, logs, commands
2. **Identify the root** - Use CloudWatch logs, AWS console, error traces
3. **Check for understanding** - Explain what you think is happening and confirm it with the student
4. **Propose the minimum solution** - Change ONE thing at a time
5. **Test and verify** - Confirm it works before continuing

### 3. **Common Causes (Check This First)**

Before writing code, check for these common problems:

**Docker Desktop Not Started** (very common with `package_docker.py`)
- Script fails with generic uv warning on nested projects
- The real problem is that Docker is not started
- The student may be distracted by the uv warning (this has already been fixed in the script)
- **Always asked**: "Is Docker Desktop started?"

**AWS Permissions Problems** (most common)
- Missing IAM policies for specific AWS services
- Region-specific permissions (especially for Bedrock inference profiles)
- Inference profiles require permissions in MULTIPLE regions
- **Review**: IAM policies, AWS region configuration, access to models in Bedrock

**Terraform Variables Not Configured**
- Each terraform directory needs its own `terraform.tfvars`
- Missing or incorrect variables generate confusing errors
- **Check**: Does `terraform.tfvars` exist? Are all the necessary variables there?

**AWS Region Mismatches**
- Some Bedrock models only exist in specific regions
- Nova Pro requires inference profiles
- Cross-region access may require Bedrock-approved models in multiple regions
- **Fix**: Region consistency in configuration files

**Access to Model Not Granted**
- AWS Bedrock requires explicit request for model access
- Nova Pro is the recommended model (Claude Sonnet has strict usage limits)
- Access is by region; inference profiles may require multiple regions
- **Review**: Bedrock console → Access to models

### 4. **Current Strategy for Models**

**Use Nova Pro, not Claude Sonnet**
- Nova Pro (`us.amazon.nova-pro-v1:0` or `eu.amazon.nova-pro-v1:0`) is the recommended model
- Requires inference profiles for cross-region access
- Claude Sonnet has too strict usage limits
- Students must request access in the Bedrock console, and possibly for multiple regions

### 5. **Test Methodology**

Each agent directory has two test files:
- `test_simple.py` - Local test with mocks (use `MOCK_LAMBDAS=true`)
- `test_full.py` - Test after deployment to AWS (current Lambda invocation)

Students must:
1. Test first locally with `test_simple.py`
2. Deploy with terraform/packaging
3. Test after deployment with `test_full.py`

### 6. **Help Students Self-Help**

Encourage students to:
- Read error messages carefully (especially CloudWatch logs)
- Check the AWS console to verify that the resources exist
- Use `terraform output` to view resource details
- Test incrementally (don't deploy everything at once)
- Monitor AWS costs (remind them to destroy resources if they are not actively using them)

---

## Terraform Strategy

### Independent Directory Architecture

Each terraform directory (2_sagemaker, 3_ingestion, etc.) is **independent** with:
- Your own local state file (`terraform.tfstate`)
- Your own `terraform.tfvars` configuration
- No dependencies between terraform directories

**This is intentional** for educational reasons:
- Allows you to deploy in parts, guide by guide
- State files are local (simpler than with remote S3)
- Each part can be destroyed independently
- No need to configure complex state buckets
- Infrastructure can be removed step by step

### Critical Requirements

**⚠️ Students MUST set `terraform.tfvars` in each directory before running terraform apply**

It is common to use Cursor's File Explorer to copy terraform.tfvars.example to terraform.tfvars and then modify the variables in each folder.

If `terraform.tfvars` is missing or incorrect:
- Terraform will use default values ​​(often wrong)
- Resources may crash with confusing errors
- Connections between services will be broken

### State Management in Terraform

- State files are automatically `.gitignored`
- Local state avoids need for S3 bucket
- You can do `terraform destroy` on each directory without affecting others
- If they lose state, it may be necessary to import resources or recreate

## Agent Strategy - about OpenAI Agents SDK

Each agent subdirectory follows a common structure and language patterns.

1. `lambda_handler.py` for lambda function and agent execution
2. `agent.py` for agent creation and logic
3. `templates.py` for prompts

Alex uses OpenAI Agents SDK. Make sure to always use the latest SDK language APIs, remembering that it is a new framework. Although it is already installed in the uv projects, the correct package name is `openai-agents` and not `agents`. Therefore, if you create a new project, use `uv add openai-agents` and this import: `from agents import Agent, Runner, trace`.

Alex uses LiteLLM to connect with Bedrock:

`model = LitellmModel(model=f"bedrock/{model_id}")`

Structured outputs and Tool calling are used, but due to a current limitation with LiteLLM and Bedrock, the same agent cannot use both at the same time. So each agent either implements structured outputs or uses Tools, never both.

This is the standard approach used in lambda_handler:

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

In cases where a Tool needs to know the authenticated user to make the correct query to the database, we use a standard, idiomatic approach to passing the context to the Tool recommended by the OpenAI Agents SDK:

```python

with trace("Reporter Agent"):
        agent = Agent[ReporterContext]( # Specify context type
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

IMPORTANT: If you use Bedrock through LiteLLM, LiteLLM requires this environment variable to be set:
`os.environ["AWS_REGION_NAME"] = bedrock_region`
This can be confusing, as other services use `"AWS_REGION"` or `"DEFAULT_AWS_REGION"`. LiteLLM needs `AWS_REGION_NAME` as documented here: https://docs.litellm.ai/docs/providers/bedrock.

---

## Common Problems and Troubleshooting

The most common are problems with the AWS region: check environment variables, terraform settings (everything should come from tfvars)!

### Problema 1: Falla `package_docker.py`

**Symptoms**: Script fails with uv warning on nested projects and perhaps an error

**Common Cause**: Docker Desktop not started or denial of Docker mounts

**Diagnosis**:
1. Question: "Is Docker Desktop running?"
2. Check: Is `docker ps` working correctly?
3. Recent fix: Script now gives better error messages, old versions don't

**Solution**: Start Docker Desktop, wait for it to load completely and try again

**If the error is Mounts Denied**: Failure to mount the /tmp directory in Docker due to permissions. Going to Docker Desktop, adding the error directory to the shared paths (Settings -> Resources -> File Sharing) solved it for a student.

**Not a solution**: Change the uv config (this is not relevant)

### Issue 2: Region Issues and Bedrock Model Access Denied

**Symptoms**: "Access denied" or "Model not found" when running agents

**Cause**: Access to model not granted in Bedrock, or incorrect region

**Diagnosis**:
1. What model are you trying to use?
2. What region does the code run in?
3. Was access to the model requested in the Bedrock console?
4. For inference profiles: Permissions in multiple regions?
5. Are the environment variables okay? LiteLLM requires `AWS_REGION_NAME`. Check that there are no hardcoded values ​​​​and that tfvars are correct. Add logs to see which region is used.

**Solution**:
1. Go to the Bedrock console in the correct region
2. Click on "Access to models"
3. Request access to Nova Pro
4. For multi-region: configure inference profiles with permissions in multiple regions

### Problema 3: Falla `terraform apply`

**Symptoms**: Resources not created, dependency errors, ARN not found

**Cause**: `terraform.tfvars` is not configured, or values ​​are missing from previous guides

**Diagnosis**:
1. Does `terraform.tfvars` exist in this directory?
2. Are all the necessary variables present? (see `terraform.tfvars.example`)
3. For advanced guides: Do you have the outputs of previous guides?
4. Run `terraform output` on those directories to get the ARNs

**Solution**:
1. Copy `terraform.tfvars.example` to `terraform.tfvars`
2. Fill in all required values
3. Get the ARNs with: `cd terraform/X_previous && terraform output`
4. Update the `.env` for Python scripts

### Problem 4: Failed Lambdas

**Symptoms**: 500 errors, timeouts, "Module not found"

**Cause**: Poorly constructed package, missing env vars, incorrect IAM

**Diagnosis**:
1. View logs in CloudWatch: `aws logs tail /aws/lambda/alex-{agent-name} --follow`
2. Check environment variables in Lambda console
3. Does the IAM role have the permissions?
4. Is Lambda packaged with Docker for linux/amd64?

**Solutions**:
1. Packaging: Re-run `package_docker.py` with Docker started
2. Env vars: Check them in console or `terraform.tfvars`
3. IAM: review policy in terraform

### Problem 5: Connection to Aurora database fails

**Symptoms**: "Cluster not found", "Secret not found", Data API errors

**Cause**: Uninitialized database, incorrect ARNs, or disabled Data API

**Diagnosis**:
1. Cluster status: `aws rds describe-db-clusters`
2. Is Data API enabled? (must put `EnableHttpEndpoint: true`)
3. Check the RNAs in environment variables
4. Is the database still initializing? (takes 10-15 min)

**Solutions**:
1. Wait to see "available" in the cluster
2. Check the Data API in the RDS console
3. Run `terraform output` on `5_database` for correct ARNs
4. Update env vars with the current ARNs

---

##Architecture Technical Summary

### Main Services by Guide

**Guides 1-2**: Fundamentals
- IAM permissions
- SageMaker Serverless Endpoint (embeddings)

**Guide 3**: Vector Storage
- Bucket S3 Vectors and index
- Lambda Ingestion
- API Gateway + API key

**Guide 4**: Investigation Agent
- App Runner Service (Researcher)
- ECR Repository
- EventBridge scheduler (optional)

**Guide 5**: Database
- Aurora Serverless v2 PostgreSQL
- Data API enabled
- Secrets Manager for credentials
- Schema and seed data database - **IMPORTANT** read the schema

**Guide 6**: Agents Orchestra (the main one)
- 5 lambdas: Planner, Tagger, Reporter, Charter, Retirement
- Each lambda using OpenAI Agents SDK with simple code. See implementations for details.
- SQS for orchestration
- S3 bucket for packets (>50MB)
- IAM permissions between services

**Guide 7**: Frontend
- Static NextJS site on S3
- CDN CloudFront
- API Gateway + Lambda backend
- Clerk Authentication

**Guide 8**: Enterprise
- CloudWatch Dashboards
- Alarms and monitoring
- LangFuse Observability
- Advanced logging

### Agent Collaboration Pattern

```
User Request → SQS → Planner
                             ├─→ Tagger (if necessary)
                             ├─→ Reporter ──┐
                             ├─→ Charter ───┼─→ Results → Database
                             └─→ Retirement ┘
```

### Cost Management

**Cost optimization**:
- Destroy Aurora by not working (greater savings)
- Use `terraform destroy` on each directory
- Monitor costs in Cost Explorer

### Cleaning Process

```bash
# Destroy in reverse order (optional, but cleaner)
cd terraform/8_enterprise && terraform destroy
cd terraform/7_frontend && terraform destroy
cd terraform/6_agents && terraform destroy
cd terraform/5_database && terraform destroy # Bigger savings
cd terraform/4_researcher && terraform destroy
cd terraform/3_ingestion && terraform destroy
cd terraform/2_sagemaker && terraform destroy
```

---

## Key Files that Students Edit

### Configuration Files
- `.env` - Root environment variables (add values ​​as per guide)
- `frontend/.env.local` - Clerk configuration on the frontend
- `terraform/*/terraform.tfvars` - Each terraform folder (copy from .example)

### Code Files That Can Modify
- `backend/researcher/server.py` - Region and model configuration (Guide 4) - this should come from variables, no code change required normally
- Agent templates in `backend/*/templates.py` - For customization
- Frontend pages for UI changes

---

##Looking for Help

### For Students

If you get stuck:

1. **Review the guide well** - Almost all the steps have troubleshooting
2. **Check error messages** - Look at CloudWatch logs, not just the terminal
3. **Check prerequisites** - Is Docker up and running? Do you have permissions? Is terraform.tfvars configured?
4. **Contact the instructor**:
   - **Ask in Frogames Training** - Includes the guide/day, error message and what you tried
   - **Email for Juan Gabriel**: juangabriel@frogames.es

Include when you ask for help:
- Guide/day you are on
- Exact error message (paste and don't summarize)
-What command did you execute?
- Relevant CloudWatch logs if you have them
-What have you already tried?

### For Claude Code (AI Assistant)

When you help students:

0. **Be Prepared** - Read all the guides to be informed
1. **Establishes the context** - Guide? Aim?
2. **Get error details** - Messages, logs, console
3. **Diagnose first** - Don't write code without understanding the problem
4. **Think incrementally** - One change at a time
5. **Check understanding** - Explain first what you think is happening before changing anything
6. **Simplify** - Don't over-engineer solutions

**Remember**: Students are learning. The goal is for them to understand what went wrong and how to fix it, not just cover up the mistake.

---

### Course Context
- Instructor: Juan Gabriel Gomila
- Platform: Frogames Training
- Course: AI in Production
- Project: "Alex" - Capstone of weeks 3-4

---

*This guide was created to help assistants (like Claude Code) effectively support Alex Project students. Last update: October 2025*
