terraform {
  required_version = ">= 1.5"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  # Usando backend local - el estado se almacenará en terraform.tfstate en este directorio
  # Esto se ignora automáticamente en git por seguridad
}

provider "aws" {
  region = var.aws_region
}

# Fuente de datos para la identidad actual del llamador
data "aws_caller_identity" "current" {}

# ========================================
# Cola SQS para procesamiento asíncrono de trabajos
# ========================================

resource "aws_sqs_queue" "analysis_jobs" {
  name                       = "alex-analysis-jobs"
  delay_seconds             = 0
  max_message_size          = 262144
  message_retention_seconds = 86400  # 1 día
  receive_wait_time_seconds = 10     # Long polling
  visibility_timeout_seconds = 910   # 15 minutos + 10 segundos de buffer (coincide con el timeout de la Lambda Planner)
  
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.analysis_jobs_dlq.arn
    maxReceiveCount     = 3
  })
  
  tags = {
    Project = "alex"
    Part    = "6"
  }
}

resource "aws_sqs_queue" "analysis_jobs_dlq" {
  name = "alex-analysis-jobs-dlq"
  
  tags = {
    Project = "alex"
    Part    = "6"
  }
}

# ========================================
# Rol IAM para funciones Lambda
# ========================================

resource "aws_iam_role" "lambda_agents_role" {
  name = "alex-lambda-agents-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
  
  tags = {
    Project = "alex"
    Part    = "6"
  }
}

# Política IAM para los agentes Lambda
resource "aws_iam_role_policy" "lambda_agents_policy" {
  name = "alex-lambda-agents-policy"
  role = aws_iam_role.lambda_agents_role.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # CloudWatch Logs
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:*"
      },
      # Acceso SQS para el orquestador
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = aws_sqs_queue.analysis_jobs.arn
      },
      # Invocación Lambda para que el orquestador llame a otros agentes
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = "arn:aws:lambda:${var.aws_region}:${data.aws_caller_identity.current.account_id}:function:alex-*"
      },
      # Acceso a Aurora Data API
      {
        Effect = "Allow"
        Action = [
          "rds-data:ExecuteStatement",
          "rds-data:BatchExecuteStatement",
          "rds-data:BeginTransaction",
          "rds-data:CommitTransaction",
          "rds-data:RollbackTransaction"
        ]
        Resource = var.aurora_cluster_arn
      },
      # Secrets Manager para credenciales de base de datos
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = var.aurora_secret_arn
      },
      # Acceso a S3 Vectors para todos los agentes
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${var.vector_bucket}",
          "arn:aws:s3:::${var.vector_bucket}/*"
        ]
      },
      # Acceso a la API S3 Vectors para todos los agentes
      {
        Effect = "Allow"
        Action = [
          "s3vectors:QueryVectors",
          "s3vectors:GetVectors"
        ]
        Resource = "arn:aws:s3vectors:${var.aws_region}:${data.aws_caller_identity.current.account_id}:bucket/${var.vector_bucket}/index/*"
      },
      # Acceso al endpoint SageMaker para el agente reporter
      {
        Effect = "Allow"
        Action = [
          "sagemaker:InvokeEndpoint"
        ]
        Resource = "arn:aws:sagemaker:${var.aws_region}:${data.aws_caller_identity.current.account_id}:endpoint/${var.sagemaker_endpoint}"
      },
      # Acceso Bedrock para todos los agentes
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Resource = [
          "arn:aws:bedrock:${var.bedrock_region}::foundation-model/*",
          "arn:aws:bedrock:${var.bedrock_region}:*:inference-profile/*"
        ]
        /*Resource = ["*"] Cambiar por esta línea si el ser tan granular en los permisos te da errores de acceso al modelo por región*/
      }
    ]
  })
}

# Adjuntar rol básico de ejecución para Lambda
resource "aws_iam_role_policy_attachment" "lambda_agents_basic" {
  role       = aws_iam_role.lambda_agents_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# ========================================
# Bucket S3 para despliegues de Lambda
# ========================================

# Bucket S3 para paquetes de Lambda (los paquetes > 50MB deben usar S3)
resource "aws_s3_bucket" "lambda_packages" {
  bucket = "alex-lambda-packages-${data.aws_caller_identity.current.account_id}"
  
  tags = {
    Project = "alex"
    Part    = "6"
  }
}

# Subir paquetes Lambda a S3
resource "aws_s3_object" "lambda_packages" {
  for_each = toset(["planner", "tagger", "reporter", "charter", "retirement"])
  
  bucket = aws_s3_bucket.lambda_packages.id
  key    = "${each.key}/${each.key}_lambda.zip"
  source = "${path.module}/../../backend/${each.key}/${each.key}_lambda.zip"
  etag   = fileexists("${path.module}/../../backend/${each.key}/${each.key}_lambda.zip") ? filemd5("${path.module}/../../backend/${each.key}/${each.key}_lambda.zip") : null
  
  tags = {
    Project = "alex"
    Part    = "6"
    Agent   = each.key
  }
}

# ========================================
# Funciones Lambda para cada agente
# ========================================

# Lambda Planner (Orquestador)
resource "aws_lambda_function" "planner" {
  function_name = "alex-planner"
  role          = aws_iam_role.lambda_agents_role.arn
  
  # Usando S3 para el paquete de despliegue (>50MB)
  s3_bucket        = aws_s3_bucket.lambda_packages.id
  s3_key           = aws_s3_object.lambda_packages["planner"].key
  source_code_hash = fileexists("${path.module}/../../backend/planner/planner_lambda.zip") ? filebase64sha256("${path.module}/../../backend/planner/planner_lambda.zip") : null
  
  handler     = "lambda_handler.lambda_handler"
  runtime     = "python3.13"
  timeout     = 900  # 15 minutos para planner
  memory_size = 2048  # 2GB para planner
  
  environment {
    variables = {
      AURORA_CLUSTER_ARN = var.aurora_cluster_arn
      AURORA_SECRET_ARN  = var.aurora_secret_arn
      DATABASE_NAME      = "alex"
      VECTOR_BUCKET      = var.vector_bucket
      BEDROCK_MODEL_ID   = var.bedrock_model_id
      BEDROCK_REGION     = var.bedrock_region
      DEFAULT_AWS_REGION = var.aws_region
      SAGEMAKER_ENDPOINT = var.sagemaker_endpoint
      POLYGON_API_KEY    = var.polygon_api_key
      POLYGON_PLAN       = var.polygon_plan
      # Observabilidad LangFuse (opcional)
      LANGFUSE_PUBLIC_KEY = var.langfuse_public_key
      LANGFUSE_SECRET_KEY = var.langfuse_secret_key
      LANGFUSE_HOST       = var.langfuse_host
      OPENAI_API_KEY      = var.openai_api_key
    }
  }

  tags = {
    Project = "alex"
    Part    = "6"
    Agent   = "orchestrator"
  }
  
  depends_on = [aws_s3_object.lambda_packages["planner"]]
}

# Trigger SQS para Planner
resource "aws_lambda_event_source_mapping" "planner_sqs" {
  event_source_arn = aws_sqs_queue.analysis_jobs.arn
  function_name    = aws_lambda_function.planner.arn
  batch_size       = 1
}

# Lambda Tagger
resource "aws_lambda_function" "tagger" {
  function_name = "alex-tagger"
  role          = aws_iam_role.lambda_agents_role.arn

  # Usando S3 para el paquete de despliegue (>50MB)
  s3_bucket        = aws_s3_bucket.lambda_packages.id
  s3_key           = aws_s3_object.lambda_packages["tagger"].key
  source_code_hash = fileexists("${path.module}/../../backend/tagger/tagger_lambda.zip") ? filebase64sha256("${path.module}/../../backend/tagger/tagger_lambda.zip") : null

  handler     = "lambda_handler.lambda_handler"
  runtime     = "python3.13"
  timeout     = 300  # 5 minutos para tagger
  memory_size = 1024

  environment {
    variables = {
      AURORA_CLUSTER_ARN = var.aurora_cluster_arn
      AURORA_SECRET_ARN  = var.aurora_secret_arn
      DATABASE_NAME      = "alex"
      BEDROCK_MODEL_ID   = var.bedrock_model_id
      BEDROCK_REGION     = var.bedrock_region
      DEFAULT_AWS_REGION = var.aws_region
      # Observabilidad LangFuse (opcional)
      LANGFUSE_PUBLIC_KEY = var.langfuse_public_key
      LANGFUSE_SECRET_KEY = var.langfuse_secret_key
      LANGFUSE_HOST       = var.langfuse_host
      OPENAI_API_KEY      = var.openai_api_key
    }
  }
  
  tags = {
    Project = "alex"
    Part    = "6"
    Agent   = "tagger"
  }
  
  depends_on = [aws_s3_object.lambda_packages["tagger"]]
}

# Lambda Reporter
resource "aws_lambda_function" "reporter" {
  function_name = "alex-reporter"
  role          = aws_iam_role.lambda_agents_role.arn
  
  # Usando S3 para el paquete de despliegue (>50MB)
  s3_bucket        = aws_s3_bucket.lambda_packages.id
  s3_key           = aws_s3_object.lambda_packages["reporter"].key
  source_code_hash = fileexists("${path.module}/../../backend/reporter/reporter_lambda.zip") ? filebase64sha256("${path.module}/../../backend/reporter/reporter_lambda.zip") : null
  
  handler     = "lambda_handler.lambda_handler"
  runtime     = "python3.13"
  timeout     = 300  # 5 minutos para el agente reporter
  memory_size = 1024
  
  environment {
    variables = {
      AURORA_CLUSTER_ARN = var.aurora_cluster_arn
      AURORA_SECRET_ARN  = var.aurora_secret_arn
      DATABASE_NAME      = "alex"
      BEDROCK_MODEL_ID   = var.bedrock_model_id
      BEDROCK_REGION     = var.bedrock_region
      DEFAULT_AWS_REGION = var.aws_region
      SAGEMAKER_ENDPOINT = var.sagemaker_endpoint
      # Observabilidad LangFuse (opcional)
      LANGFUSE_PUBLIC_KEY = var.langfuse_public_key
      LANGFUSE_SECRET_KEY = var.langfuse_secret_key
      LANGFUSE_HOST       = var.langfuse_host
      OPENAI_API_KEY      = var.openai_api_key
    }
  }

  tags = {
    Project = "alex"
    Part    = "6"
    Agent   = "reporter"
  }
  
  depends_on = [aws_s3_object.lambda_packages["reporter"]]
}

# Lambda Charter
resource "aws_lambda_function" "charter" {
  function_name = "alex-charter"
  role          = aws_iam_role.lambda_agents_role.arn
  
  # Usando S3 para el paquete de despliegue (>50MB)
  s3_bucket        = aws_s3_bucket.lambda_packages.id
  s3_key           = aws_s3_object.lambda_packages["charter"].key
  source_code_hash = fileexists("${path.module}/../../backend/charter/charter_lambda.zip") ? filebase64sha256("${path.module}/../../backend/charter/charter_lambda.zip") : null
  
  handler     = "lambda_handler.lambda_handler"
  runtime     = "python3.13"
  timeout     = 300  # 5 minutos para el agente charter
  memory_size = 1024
  
  environment {
    variables = {
      AURORA_CLUSTER_ARN = var.aurora_cluster_arn
      AURORA_SECRET_ARN  = var.aurora_secret_arn
      DATABASE_NAME      = "alex"
      BEDROCK_MODEL_ID   = var.bedrock_model_id
      BEDROCK_REGION     = var.bedrock_region
      DEFAULT_AWS_REGION = var.aws_region
      # Observabilidad LangFuse (opcional)
      LANGFUSE_PUBLIC_KEY = var.langfuse_public_key
      LANGFUSE_SECRET_KEY = var.langfuse_secret_key
      LANGFUSE_HOST       = var.langfuse_host
      OPENAI_API_KEY      = var.openai_api_key
    }
  }

  tags = {
    Project = "alex"
    Part    = "6"
    Agent   = "charter"
  }
  
  depends_on = [aws_s3_object.lambda_packages["charter"]]
}

# Lambda Retirement
resource "aws_lambda_function" "retirement" {
  function_name = "alex-retirement"
  role          = aws_iam_role.lambda_agents_role.arn
  
  # Usando S3 para el paquete de despliegue (>50MB)
  s3_bucket        = aws_s3_bucket.lambda_packages.id
  s3_key           = aws_s3_object.lambda_packages["retirement"].key
  source_code_hash = fileexists("${path.module}/../../backend/retirement/retirement_lambda.zip") ? filebase64sha256("${path.module}/../../backend/retirement/retirement_lambda.zip") : null
  
  handler     = "lambda_handler.lambda_handler"
  runtime     = "python3.13"
  timeout     = 300  # 5 minutos para el agente retirement
  memory_size = 1024
  
  environment {
    variables = {
      AURORA_CLUSTER_ARN = var.aurora_cluster_arn
      AURORA_SECRET_ARN  = var.aurora_secret_arn
      DATABASE_NAME      = "alex"
      BEDROCK_MODEL_ID   = var.bedrock_model_id
      BEDROCK_REGION     = var.bedrock_region
      DEFAULT_AWS_REGION = var.aws_region
      # Observabilidad LangFuse (opcional)
      LANGFUSE_PUBLIC_KEY = var.langfuse_public_key
      LANGFUSE_SECRET_KEY = var.langfuse_secret_key
      LANGFUSE_HOST       = var.langfuse_host
      OPENAI_API_KEY      = var.openai_api_key
    }
  }

  tags = {
    Project = "alex"
    Part    = "6"
    Agent   = "retirement"
  }
  
  depends_on = [aws_s3_object.lambda_packages["retirement"]]
}

# Grupos de logs de CloudWatch
resource "aws_cloudwatch_log_group" "agent_logs" {
  for_each = toset(["planner", "tagger", "reporter", "charter", "retirement"])
  
  name              = "/aws/lambda/alex-${each.key}"
  retention_in_days = 7
  
  tags = {
    Project = "alex"
    Part    = "6"
    Agent   = each.key
  }
}