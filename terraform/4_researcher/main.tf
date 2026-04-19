terraform {
  required_version = ">= 1.5"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  # Usando backend local - el estado se almacenará en terraform.tfstate en este directorio
  # Esto está agregado automáticamente al .gitignore por seguridad
}

provider "aws" {
  region = var.aws_region
}

# Fuente de datos para la identidad actual del llamador
data "aws_caller_identity" "current" {}

# ========================================
# Repositorio ECR
# ========================================

# Repositorio ECR para la imagen Docker de researcher
resource "aws_ecr_repository" "researcher" {
  name                 = "alex-researcher"
  image_tag_mutability = "MUTABLE"
  force_delete         = true  # Permite borrar incluso si hay imágenes
  
  image_scanning_configuration {
    scan_on_push = false
  }
  
  tags = {
    Project = "alex"
    Part    = "4"
  }
}

# ========================================
# Servicio App Runner
# ========================================

# Rol IAM para App Runner
resource "aws_iam_role" "app_runner_role" {
  name = "alex-app-runner-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "build.apprunner.amazonaws.com"
        }
      },
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "tasks.apprunner.amazonaws.com"
        }
      }
    ]
  })
  
  tags = {
    Project = "alex"
    Part    = "4"
  }
}

# Política para que App Runner acceda a ECR
resource "aws_iam_role_policy_attachment" "app_runner_ecr_access" {
  role       = aws_iam_role.app_runner_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess"
}

# Rol IAM para la instancia de App Runner (acceso en tiempo de ejecución a servicios de AWS)
resource "aws_iam_role" "app_runner_instance_role" {
  name = "alex-app-runner-instance-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "tasks.apprunner.amazonaws.com"
        }
      }
    ]
  })
  
  tags = {
    Project = "alex"
    Part    = "4"
  }
}

# Política para que la instancia de App Runner acceda a Bedrock
resource "aws_iam_role_policy" "app_runner_instance_bedrock_access" {
  name = "alex-app-runner-instance-bedrock-policy"
  role = aws_iam_role.app_runner_instance_role.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
          "bedrock:ListFoundationModels"
        ]
        Resource = "*"
      }
    ]
  })
}

# Servicio App Runner
resource "aws_apprunner_service" "researcher" {
  service_name = "alex-researcher"
  
  source_configuration {
    auto_deployments_enabled = false
    
    # Configurar autenticación para repositorio ECR privado
    authentication_configuration {
      access_role_arn = aws_iam_role.app_runner_role.arn
    }
    
    image_repository {
      image_identifier      = "${aws_ecr_repository.researcher.repository_url}:latest"
      image_configuration {
        port = "8000"
        runtime_environment_variables = {
          OPENAI_API_KEY    = var.openai_api_key
          ALEX_API_ENDPOINT = var.alex_api_endpoint
          ALEX_API_KEY      = var.alex_api_key
        }
      }
      image_repository_type = "ECR"
    }
  }
  
  instance_configuration {
    cpu    = "1 vCPU"
    memory = "2 GB"
    instance_role_arn = aws_iam_role.app_runner_instance_role.arn
  }
  
  tags = {
    Project = "alex"
    Part    = "4"
  }
}

# ========================================
# Programador EventBridge (Opcional)
# ========================================

# Rol IAM para EventBridge
resource "aws_iam_role" "eventbridge_role" {
  count = var.scheduler_enabled ? 1 : 0
  name  = "alex-eventbridge-scheduler-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "scheduler.amazonaws.com"
        }
      }
    ]
  })
  
  tags = {
    Project = "alex"
    Part    = "4"
  }
}

# Función Lambda para invocar researcher
resource "aws_lambda_function" "scheduler_lambda" {
  count         = var.scheduler_enabled ? 1 : 0
  function_name = "alex-researcher-scheduler"
  role          = aws_iam_role.lambda_scheduler_role[0].arn
  
  # Nota: El paquete de despliegue se creará siguiendo las instrucciones de la guía
  filename         = "${path.module}/../../backend/scheduler/lambda_function.zip"
  source_code_hash = fileexists("${path.module}/../../backend/scheduler/lambda_function.zip") ? filebase64sha256("${path.module}/../../backend/scheduler/lambda_function.zip") : null
  
  handler     = "lambda_function.handler"
  runtime     = "python3.13"
  timeout     = 180  # 3 minutos para manejar el tiempo de respuesta de App Runner
  memory_size = 256
  
  environment {
    variables = {
      APP_RUNNER_URL = aws_apprunner_service.researcher.service_url
    }
  }
  
  tags = {
    Project = "alex"
    Part    = "4"
  }
}

# Rol IAM para la Lambda del programador
resource "aws_iam_role" "lambda_scheduler_role" {
  count = var.scheduler_enabled ? 1 : 0
  name  = "alex-scheduler-lambda-role"
  
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
    Part    = "4"
  }
}

# Política básica de ejecución para Lambda
resource "aws_iam_role_policy_attachment" "lambda_scheduler_basic" {
  count      = var.scheduler_enabled ? 1 : 0
  role       = aws_iam_role.lambda_scheduler_role[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Programación en EventBridge
resource "aws_scheduler_schedule" "research_schedule" {
  count = var.scheduler_enabled ? 1 : 0
  name  = "alex-research-schedule"
  
  flexible_time_window {
    mode = "OFF"
  }
  
  schedule_expression = "rate(2 hours)"
  
  target {
    arn      = aws_lambda_function.scheduler_lambda[0].arn
    role_arn = aws_iam_role.eventbridge_role[0].arn
  }
}

# Permiso para que EventBridge invoque Lambda
resource "aws_lambda_permission" "allow_eventbridge" {
  count         = var.scheduler_enabled ? 1 : 0
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.scheduler_lambda[0].function_name
  principal     = "scheduler.amazonaws.com"
  source_arn    = aws_scheduler_schedule.research_schedule[0].arn
}

# Política para que EventBridge invoque Lambda
resource "aws_iam_role_policy" "eventbridge_invoke_lambda" {
  count = var.scheduler_enabled ? 1 : 0
  name  = "InvokeLambdaPolicy"
  role  = aws_iam_role.eventbridge_role[0].id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = aws_lambda_function.scheduler_lambda[0].arn
      }
    ]
  })
}