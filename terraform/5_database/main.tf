terraform {
  required_version = ">= 1.5"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }
  
  # Usando backend local - el estado se almacenará en terraform.tfstate en este directorio
  # Esto es automáticamente ignorado por git por seguridad
}

provider "aws" {
  region = var.aws_region
}

# Fuente de datos para la identidad actual del llamador
data "aws_caller_identity" "current" {}

# ========================================
# Cluster Aurora Serverless v2 PostgreSQL
# ========================================

# Contraseña aleatoria para la base de datos
resource "random_password" "db_password" {
  length  = 32
  special = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

# Secreto de Secrets Manager para credenciales de base de datos
resource "aws_secretsmanager_secret" "db_credentials" {
  name                    = "alex-aurora-credentials-${random_id.suffix.hex}"
  recovery_window_in_days = 0  # Para desarrollo - eliminación inmediata
  
  tags = {
    Project = "alex"
    Part    = "5"
  }
}

resource "random_id" "suffix" {
  byte_length = 4
}

resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = aws_secretsmanager_secret.db_credentials.id
  secret_string = jsonencode({
    username = "alexadmin"
    password = random_password.db_password.result
  })
}

# Grupo de subredes de BD (usando VPC por defecto)
data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

resource "aws_db_subnet_group" "aurora" {
  name       = "alex-aurora-subnet-group"
  subnet_ids = data.aws_subnets.default.ids
  
  tags = {
    Project = "alex"
    Part    = "5"
  }
}

# Grupo de seguridad para Aurora
resource "aws_security_group" "aurora" {
  name        = "alex-aurora-sg"
  description = "Grupo de seguridad para el cluster Aurora de Alex"
  vpc_id      = data.aws_vpc.default.id
  
  # Permitir acceso PostgreSQL desde dentro de la VPC
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [data.aws_vpc.default.cidr_block]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = {
    Project = "alex"
    Part    = "5"
  }
}

# Clúster Aurora Serverless v2
resource "aws_rds_cluster" "aurora" {
  cluster_identifier     = "alex-aurora-cluster"
  engine                 = "aurora-postgresql"
  engine_mode            = "provisioned"
  engine_version         = "15.12"
  database_name          = "alex"
  master_username        = "alexadmin"
  master_password        = random_password.db_password.result
  
  # Configuración de escalado serverless v2
  serverlessv2_scaling_configuration {
    min_capacity = var.min_capacity
    max_capacity = var.max_capacity
  }
  
  # Habilitar API de datos
  enable_http_endpoint = true
  
  # Red
  db_subnet_group_name   = aws_db_subnet_group.aurora.name
  vpc_security_group_ids = [aws_security_group.aurora.id]
  
  # Copia de seguridad y mantenimiento
  backup_retention_period   = 7
  preferred_backup_window   = "03:00-04:00"
  preferred_maintenance_window = "sun:04:00-sun:05:00"
  
  # Configuración de desarrollo
  skip_final_snapshot = true
  apply_immediately   = true
  
  tags = {
    Project = "alex"
    Part    = "5"
  }
}

# Instancia Aurora Serverless v2
resource "aws_rds_cluster_instance" "aurora" {
  identifier          = "alex-aurora-instance-1"
  cluster_identifier  = aws_rds_cluster.aurora.id
  instance_class      = "db.serverless"
  engine              = aws_rds_cluster.aurora.engine
  engine_version      = aws_rds_cluster.aurora.engine_version
  
  performance_insights_enabled = false  # Ahorrar costos en desarrollo
  
  tags = {
    Project = "alex"
    Part    = "5"
  }
}

# Rol IAM para Lambda para acceder a Aurora Data API
resource "aws_iam_role" "lambda_aurora_role" {
  name = "alex-lambda-aurora-role"
  
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
    Part    = "5"
  }
}

# Política IAM para acceso a Data API
resource "aws_iam_role_policy" "lambda_aurora_policy" {
  name = "alex-lambda-aurora-policy"
  role = aws_iam_role.lambda_aurora_role.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "rds-data:ExecuteStatement",
          "rds-data:BatchExecuteStatement",
          "rds-data:BeginTransaction",
          "rds-data:CommitTransaction",
          "rds-data:RollbackTransaction"
        ]
        Resource = aws_rds_cluster.aurora.arn
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = aws_secretsmanager_secret.db_credentials.arn
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:*"
      }
    ]
  })
}

# Adjuntar rol básico de ejecución para Lambda
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_aurora_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}
