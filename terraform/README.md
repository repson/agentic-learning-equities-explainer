# Terraform Infrastructure

This directory contains the Terraform configurations for the Alex Financial Planner project.

## Structure

Each part of the course has its own independent Terraform directory:

- **`2_sagemaker/`** - SageMaker serverless endpoint for embeddings (Guide 2)
- **`3_ingestion/`** - S3 Vectors, Lambda, and API Gateway for document ingestion (Guide 3)
- **`4_researcher/`** - App Runner service for the AI researcher agent (Guide 4)
- **`5_database/`** - Aurora Serverless v2 PostgreSQL with Data API (Guide 5)
- **`6_agents/`** - Lambda functions for the agent orchestrator (Guide 6)
- **`7_frontend/`** - API Lambda and frontend infrastructure (Guide 7)
- **`8_observability/`** - LangFuse and monitoring setup (Guide 8)

## Key Design Decisions

### Why separate directories?

1. **Educational clarity**: Each guide maps exactly to one Terraform directory
2. **Independent deployment**: Students can deploy each part without affecting the others
3. **Risk reduction**: Errors in one part do not impact previously deployed infrastructure
4. **Progressive learning**: Later parts cannot be accidentally deployed before completing earlier ones

### Why local state?

1. **Simplicity**: No need to configure or manage an S3 bucket for state
2. **Zero dependencies**: You can start deploying immediately with no prior infrastructure
3. **Cost savings**: No S3 storage costs for state files
4. **Security**: State files are automatically listed in `.gitignore`

## Usage

For each part of the course:

```bash
# Navigate to the specific part directory
cd terraform/2_sagemaker  # (or 3_ingestion, 4_researcher, etc.)

# Initialize Terraform (only required once per directory)
terraform init

# Review what will be created
terraform plan

# Deploy infrastructure
terraform apply

# When you finish with that part (optional)
terraform destroy
```

## Environment Variables

Some Terraform configurations require environment variables from your `.env` file:

- `OPENAI_API_KEY` - For the researcher agent (Part 4)
- `ALEX_API_ENDPOINT` - API Gateway endpoint (from Part 3)
- `ALEX_API_KEY` - API key for ingestion (from Part 3)
- `AURORA_CLUSTER_ARN` - Aurora cluster ARN (from Part 5)
- `AURORA_SECRET_ARN` - Secrets Manager ARN (from Part 5)
- `VECTOR_BUCKET` - S3 Vectors bucket name (from Part 3)
- `BEDROCK_MODEL_ID` - Bedrock model to use (Part 6)

## State Management

- Each directory maintains its own `terraform.tfstate` file
- State files are stored locally (not in S3)
- All `*.tfstate` files are listed in `.gitignore` for security
- Back up state files before making major changes

## Production Considerations

This structure is optimized for learning. In production, you might consider:

- **Remote state**: Store state in S3 with state locking via DynamoDB
- **Modules**: Share common configuration across environments
- **Workspaces**: Manage multiple environments (dev, staging, prod)
- **CI/CD**: Automated deployment pipelines
- **Terragrunt**: Orchestrate multiple Terraform configurations

## Troubleshooting

If you run into issues:

1. **State conflicts**: Each directory has independent state. If you need to import existing resources:
   ```bash
   terraform import <resource_type>.<resource_name> <resource_id>
   ```

2. **Missing dependencies**: Make sure you completed previous guides and have the required environment variables

3. **Start from scratch**: To reset any directory:
   ```bash
   terraform destroy  # Remove resources
   rm -rf .terraform terraform.tfstate*  # Clean local files
   terraform init  # Re-initialize
   ```

## Cleanup Helper

To clean old monolithic Terraform files (if upgrading from a previous version):

```bash
cd terraform
python cleanup_old_structure.py
```

This identifies old files that can be safely removed.
