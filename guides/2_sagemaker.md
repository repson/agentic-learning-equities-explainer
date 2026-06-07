# Building Alex: Part 2 - Serverless Deployment on SageMaker

Welcome back! In this guide, we will deploy a serverless SageMaker endpoint that generates embeddings for Alex's knowledge base. This is a critical component: it converts text into numerical vectors that can be searched and compared.

## REMINDER - IMPORTANT TIP!

There is a `gameplan.md` file at the project root that describes the full Alex project for an AI Agent, so you can ask questions and get help. There are also identical files `CLAUDE.md` and `AGENTS.md`. If you need help, simply open your favorite AI Agent and give it this prompt:

> I am a student in the AI in Production course. We are in the course repository. Read the `gameplan.md` file for project context. Read this file completely and carefully review all linked guides. Do not start any work except reading and reviewing the directory structure. When you finish reading, tell me whether you have questions before we begin.

After answering questions, clearly indicate which guide you are on and any issues you encounter. Be careful to validate each suggestion; always ask for root cause and evidence for the issue. LLMs tend to jump to conclusions, but they often correct themselves when they need to provide evidence.

## Architecture Overview

## Why SageMaker?

We use SageMaker for several key reasons:
1. **Production-ready**: It handles scaling, monitoring, and availability
2. **Cost-effective**: Serverless endpoints scale to zero when idle
3. **Professional skillset**: SageMaker is widely used in enterprise AI environments

## What will we build?

We will implement:
- A SageMaker model that automatically downloads `all-MiniLM-L6-v2` from HuggingFace Hub
- A serverless endpoint that scales automatically
- Infrastructure as Code using Terraform

The beauty of this approach: no model artifact preparation is required! SageMaker's HuggingFace container handles everything.

## Prerequisites

Before starting:
- Complete [1_permissions.md](1_permissions.md)
- Have Terraform installed (version 1.5+)

## Step 1: Configure Terraform variables

First, let's prepare the Terraform configuration for this guide:

```bash
# Navigate to the SageMaker Terraform directory
cd terraform/2_sagemaker

# Copy the example variables file
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` and set your AWS region (it must match your DEFAULT_AWS_REGION):
```hcl
aws_region = "us-east-1"  # Use your DEFAULT_AWS_REGION from .env
```

## Step 2: Deploy with Terraform

Now let's deploy the SageMaker infrastructure. With the HuggingFace approach, model artifacts are not needed: the model is downloaded automatically from HuggingFace Hub.

```bash
# Initialize Terraform (creates the local state file)
terraform init

# Deploy SageMaker infrastructure
terraform apply
```

When prompted, type `yes` to confirm deployment. This creates:
- IAM role for SageMaker
- SageMaker model configuration (with the HuggingFace model)
- Serverless endpoint

## Step 3: Understand what was created

Terraform created several resources:

1. **IAM role**: Gives SageMaker the required permissions
2. **SageMaker model**: Configuration pointing to HuggingFace model `sentence-transformers/all-MiniLM-L6-v2`
3. **Serverless endpoint**: API endpoint for generating embeddings

After deployment, Terraform shows important outputs including setup instructions.

### Save your configuration

**Important**: Update your `.env` file with the endpoint name:

1. Note the endpoint name from Terraform output (it should be `alex-embedding-endpoint`)
2. Edit `.env` in Cursor
3. Update this line:
   ```
   # Part 2 - SageMaker
   SAGEMAKER_ENDPOINT=alex-embedding-endpoint
   ```

💡 **Tip**: Terraform outputs appear at the end of `terraform apply`. You can also view them anytime with:
```bash
terraform output
```

## Step 4: Test the endpoint

Let's verify the endpoint works with a simple test:

```bash
# Navigate to the backend directory where the test payload is
cd ../../backend

# Invoke the endpoint and print output directly to the console
aws sagemaker-runtime invoke-endpoint --endpoint-name alex-embedding-endpoint --content-type application/json --body fileb://vectorize_me.json --output json /dev/stdout
```

You will see a JSON array with 384 floating-point numbers; that is the text "vectorize me" converted to an embedding vector.

**Note**: The first request to a serverless endpoint can take 10-60 seconds (cold start). Subsequent requests are much faster.

## Cost analysis

Your serverless endpoint:
- **Scales to zero**: No charges when idle
- **Per-request pricing**: ~$0.00002 per compute second
- **Memory**: 3GB allocated (AWS default limit for serverless)
- **Estimated cost**: $1-2/month for typical use (1000 requests/day)

## Troubleshooting

If endpoint invocation fails:

1. **Check endpoint status**:
```bash
aws sagemaker describe-endpoint --endpoint-name alex-embedding-endpoint
```
Status should be "InService"

2. **Check CloudWatch logs**:
```bash
aws logs tail /aws/sagemaker/Endpoints/alex-embedding-endpoint --follow
```

3. **Verify the HuggingFace model ID**:
Confirm the endpoint is configured with the correct model:
```bash
aws sagemaker describe-model --model-name alex-embedding-model --query 'PrimaryContainer.Environment'
```
It should show: `{"HF_MODEL_ID": "sentence-transformers/all-MiniLM-L6-v2", "HF_TASK": "feature-extraction"}`

**Note**: If you are not in your default region, add `--region your-region` to these commands.

## Understanding serverless vs always-on

We chose serverless because:
- **Cold start**: 5-10 seconds (acceptable for our use case)
- **Cost savings**: ~$1-2/month vs $50-100/month for always-on
- **Auto-scaling**: Handles traffic spikes automatically

For production systems with strict latency requirements, you may prefer always-on endpoints.

## MLOps in SageMaker

### What is MLOps?

MLOps (Machine Learning Operations) is the practice of applying DevOps principles to machine learning systems. SageMaker is AWS's end-to-end MLOps platform, providing tools for the entire ML lifecycle: data preparation, model training, deployment, monitoring, and retraining.

In production ML systems, you need to manage:
- **Model versioning**: Track different versions as models evolve
- **A/B testing**: Compare model performance in production
- **Model monitoring**: Detect when model performance degrades
- **Automatic retraining**: Retrain models when performance drops
- **Model registry**: Central repository for approved models
- **Pipeline automation**: Orchestrate the full ML workflow

### Model drift and why it matters

**Model drift** happens when model performance degrades over time because production data differs from training data. For our embedding model, drift can happen if:
- Language evolves (new financial terms appear)
- User behavior changes (different query types)
- Market conditions change (new investment products)

SageMaker Model Monitor can automatically detect drift by:
- Analyzing prediction distributions over time
- Comparing current inputs with training data
- Alerting when statistical properties change significantly
- Triggering automatic retraining pipelines

### Explore SageMaker in the AWS Console

Let's explore what else SageMaker can do. Open the console and review these sections:

1. **Go to the SageMaker console**:
   ```
   https://console.aws.amazon.com/sagemaker/
   ```

2. **Explore key MLOps features** (left sidebar):
   - **Model Registry**: See how teams manage model versions
   - **Pipelines**: See how ML workflows are automated
   - **Model Monitor**: Review how drift detection works
   - **Experiments**: Track training runs and hyperparameters
   - **Feature Store**: Centralized feature management
   - **Ground Truth**: Data labeling service

3. **Verify your endpoint**:
   - Click "Inference" -> "Endpoints"
   - Find `alex-embedding-endpoint`
   - Click to view metrics, configuration, and monitoring options
   - Check the "Data capture" option for monitoring

4. **Explore model versions**:
   - Click "Inference" -> "Models"
   - See how SageMaker tracks model artifacts and configurations
   - Each model has a unique ARN for versioning

### SageMaker vs Bedrock: when to use each

You have already worked with Bedrock, so here's when to use each service:

| Aspect | SageMaker | Bedrock |
|---------|-----------|---------|
| **Use case** | Deploy YOUR models or fine-tuned models | Use pre-trained foundation models via API |
| **Model source** | Open source, custom-trained, or fine-tuned | AWS-managed models (Claude, Llama, etc.) |
| **Customization** | Full control of model, training, and infrastructure | Limited to prompt engineering and RAG |
| **Cost model** | Pay for infrastructure (compute hours) | Pay per API call (tokens) |
| **Setup complexity** | Higher: you manage endpoints, scaling, and monitoring | Lower: API calls only |
| **MLOps features** | Complete: versioning, monitoring, and pipelines | Minimal: usage tracking only |
| **Best for** | • Custom models<br>• Fine-tuned models<br>• Specialized embeddings<br>• Full ML pipelines | • General language tasks<br>• Rapid prototyping<br>• Standard AI capabilities |
| **Latency** | Predictable (always-on) or variable (serverless) | Generally low and consistent |
| **Scaling** | You manage it (auto-scaling available) | Fully managed by AWS |

### Decision examples from real projects

**Use SageMaker when:**
- You need a specific embedding model (like our all-MiniLM-L6-v2)
- You fine-tuned a model with your company data
- You need full control over versioning and deployment
- You want custom pre/post processing
- You need model drift monitoring
- Compliance requires local or VPC deployment

**Use Bedrock when:**
- You need general language understanding (like our Part 6 agents)
- You want rapid prototyping without infrastructure
- The task relies on prompt engineering
- You want access to state-of-the-art foundation models
- You want to minimize ongoing operations
- Token-based pricing matches your usage

### Advanced SageMaker capabilities

Beyond what we deployed, SageMaker also provides:

- **SageMaker Studio**: IDE for ML development
- **Multi-Model Endpoints**: Host multiple models on one endpoint
- **Model Compilation (Neo)**: Optimize models for specific hardware
- **Edge Deployment**: Deploy models to IoT devices
- **Distributed training**: Train large models across multiple GPUs
- **Hyperparameter tuning**: Automated parameter optimization
- **Batch Transform**: Offline processing for large datasets
- **Data Wrangler**: Visual data preparation tool

### Try this: Review model metrics

While your endpoint is running, review its CloudWatch metrics:

```bash
# View invocation metrics
aws cloudwatch get-metric-statistics --namespace "AWS/SageMaker" --metric-name "Invocations" --dimensions Name=EndpointName,Value=alex-embedding-endpoint --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) --end-time $(date -u +%Y-%m-%dT%H:%M:%S) --period 300 --statistics Sum --region $(aws configure get region)
```

This shows how SageMaker automatically tracks model usage - essential for MLOps.

## Troubleshooting

### "Endpoint Already Exists" error

If you see "Cannot create already existing endpoint" during `terraform apply`, it means the endpoint was created but Terraform lost tracking (usually because the process was interrupted). To fix it:

**Option 1: Import the existing endpoint** (recommended)
```bash
terraform import aws_sagemaker_endpoint.embedding_endpoint alex-embedding-endpoint
terraform apply
```

**Option 2: Delete and recreate**
```bash
aws sagemaker delete-endpoint --endpoint-name alex-embedding-endpoint
# Wait for deletion to complete (verify with describe-endpoint)
terraform apply
```

### Terraform apply takes too long

SageMaker serverless endpoints can take 3-5 minutes to create. Be patient and do not interrupt the process. If you interrupt it, follow "Endpoint Already Exists" above.

### Endpoint creation fails with IAM role error

If you see an invalid IAM role error during `terraform apply`, it is usually a known IAM propagation delay issue. The Terraform configuration includes a fix by adding a 15-second delay before endpoint creation so the IAM role fully propagates.

If issues continue:
1. Run `terraform destroy` to clean up
2. Wait one minute for full IAM propagation
3. Run `terraform apply` again

The error message can be misleading: it may indicate quota limits or propagation delays instead of a real IAM permission problem.

## Cleanup (optional)

If you need to delete only the SageMaker infrastructure:

```bash
cd terraform/2_sagemaker
terraform destroy
```

⚠️ This only removes SageMaker resources from this guide, not other parts.

## Next steps

Congratulations! You deployed a production-ready ML model on AWS.

In the next guide:
1. We will configure S3 Vectors for cost-effective vector storage (90% cheaper)
2. We will create a Lambda function to connect everything
3. We will build an API to ingest financial knowledge

Your SageMaker endpoint is ready and waiting. Let's continue building Alex! 🎉

Continue to: [3_ingest.md](3_ingest.md)
