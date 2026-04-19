# Parte 8: Enterprise - Paneles de CloudWatch para Monitorización

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Fuentes de datos
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

locals {
  name_prefix = "alex"

  common_tags = {
    Project   = "alex"
    Part      = "8_enterprise"
    ManagedBy = "terraform"
  }
}

# ========================================
# Panel de Uso de Bedrock y Modelos IA
# ========================================

resource "aws_cloudwatch_dashboard" "ai_model_usage" {
  dashboard_name = "${local.name_prefix}-ai-model-usage"

  dashboard_body = jsonencode({
    widgets = [
      # Invocaciones de modelo Bedrock
      {
        type   = "metric"
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/Bedrock", "Invocations", "ModelId", var.bedrock_model_id, { stat = "Sum", label = "Invocaciones de modelo", id = "m1", color = "#1f77b4" }],
            [".", "InvocationClientErrors", ".", ".", { stat = "Sum", label = "Errores de cliente", id = "m2", color = "#d62728" }],
            [".", "InvocationServerErrors", ".", ".", { stat = "Sum", label = "Errores de servidor", id = "m3", color = "#ff7f0e" }]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.bedrock_region
          title   = "Invocaciones de modelo Bedrock (${var.bedrock_model_id})"
          period  = 300
          stat    = "Sum"
          yAxis = {
            left = {
              label     = "Cantidad"
              showUnits = false
            }
          }
        }
      },
      # Uso de tokens de Bedrock
      {
        type   = "metric"
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/Bedrock", "InputTokenCount", "ModelId", var.bedrock_model_id, { stat = "Sum", label = "Tokens de entrada", id = "t1", color = "#2ca02c" }],
            [".", "OutputTokenCount", ".", ".", { stat = "Sum", label = "Tokens de salida", id = "t2", color = "#9467bd" }]
          ]
          view    = "timeSeries"
          stacked = true
          region  = var.bedrock_region
          title   = "Uso de tokens de Bedrock (${var.bedrock_model_id})"
          period  = 300
          stat    = "Sum"
          yAxis = {
            left = {
              label     = "Tokens"
              showUnits = false
            }
          }
        }
      },
      # Latencia de Bedrock
      {
        type   = "metric"
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/Bedrock", "InvocationLatency", "ModelId", var.bedrock_model_id, { stat = "Average", label = "Latencia promedio", id = "l1", color = "#1f77b4" }],
            [".", ".", ".", ".", { stat = "Maximum", label = "Latencia máx.", id = "l2", color = "#d62728" }],
            [".", ".", ".", ".", { stat = "Minimum", label = "Latencia mín.", id = "l3", color = "#2ca02c" }]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.bedrock_region
          title   = "Latencia de respuesta de Bedrock (${var.bedrock_model_id})"
          period  = 300
          yAxis = {
            left = {
              label     = "Latencia (ms)"
              showUnits = false
            }
          }
        }
      },
      # Invocaciones del endpoint de SageMaker
      {
        type   = "metric"
        width  = 12
        height = 6
        properties = {
          metrics = [
            [{ expression = "SEARCH(' {AWS/SageMaker,EndpointName,VariantName} MetricName=\"Invocations\" EndpointName=\"alex-embedding-endpoint\" ', 'Sum')", id = "s1", label = "Invocaciones", color = "#1f77b4" }],
            [{ expression = "SEARCH(' {AWS/SageMaker,EndpointName,VariantName} MetricName=\"Invocation4XXErrors\" EndpointName=\"alex-embedding-endpoint\" ', 'Sum')", id = "s2", label = "Errores 4XX", color = "#ff7f0e" }],
            [{ expression = "SEARCH(' {AWS/SageMaker,EndpointName,VariantName} MetricName=\"Invocation5XXErrors\" EndpointName=\"alex-embedding-endpoint\" ', 'Sum')", id = "s3", label = "Errores 5XX", color = "#d62728" }]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Invocaciones del endpoint de embeddings SageMaker"
          period  = 300
          yAxis = {
            left = {
              label     = "Cantidad"
              showUnits = false
            }
          }
        }
      },
      # Latencia del modelo SageMaker
      {
        type   = "metric"
        width  = 12
        height = 6
        properties = {
          metrics = [
            [{ expression = "SEARCH(' {AWS/SageMaker,EndpointName,VariantName} MetricName=\"ModelLatency\" EndpointName=\"alex-embedding-endpoint\" ', 'Average')", id = "ml1", label = "Latencia promedio", color = "#2ca02c" }],
            [{ expression = "SEARCH(' {AWS/SageMaker,EndpointName,VariantName} MetricName=\"ModelLatency\" EndpointName=\"alex-embedding-endpoint\" ', 'Maximum')", id = "ml2", label = "Latencia máx.", color = "#d62728" }],
            [{ expression = "SEARCH(' {AWS/SageMaker,EndpointName,VariantName} MetricName=\"ModelLatency\" EndpointName=\"alex-embedding-endpoint\" ', 'Minimum')", id = "ml3", label = "Latencia mín.", color = "#1f77b4" }]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Latencia del modelo SageMaker"
          period  = 300
          yAxis = {
            left = {
              label     = "Latencia (μs)"
              showUnits = false
            }
          }
        }
      }
    ]
  })

}

# ========================================
# Panel de Desempeño de Agentes
# ========================================

resource "aws_cloudwatch_dashboard" "agent_performance" {
  dashboard_name = "${local.name_prefix}-agent-performance"

  dashboard_body = jsonencode({
    widgets = [
      # Tiempos de ejecución de agentes
      {
        type   = "metric"
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/Lambda", "Duration", "FunctionName", "alex-planner", { stat = "Average", label = "Planner", id = "m1", color = "#1f77b4" }],
            [".", ".", ".", "alex-reporter", { stat = "Average", label = "Reporter", id = "m2", color = "#2ca02c" }],
            [".", ".", ".", "alex-charter", { stat = "Average", label = "Charter", id = "m3", color = "#ff7f0e" }],
            [".", ".", ".", "alex-retirement", { stat = "Average", label = "Retirement", id = "m4", color = "#d62728" }],
            [".", ".", ".", "alex-tagger", { stat = "Average", label = "Tagger", id = "m5", color = "#9467bd" }]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Tiempos de ejecución de agentes"
          period  = 300
          stat    = "Average"
          yAxis = {
            left = {
              label     = "Duración (ms)"
              showUnits = false
            }
          }
        }
      },
      # Tasas de error de los agentes
      {
        type   = "metric"
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/Lambda", "Errors", "FunctionName", "alex-planner", { stat = "Sum", label = "Errores Planner", id = "e1", color = "#1f77b4" }],
            [".", ".", ".", "alex-reporter", { stat = "Sum", label = "Errores Reporter", id = "e2", color = "#2ca02c" }],
            [".", ".", ".", "alex-charter", { stat = "Sum", label = "Errores Charter", id = "e3", color = "#ff7f0e" }],
            [".", ".", ".", "alex-retirement", { stat = "Sum", label = "Errores Retirement", id = "e4", color = "#d62728" }],
            [".", ".", ".", "alex-tagger", { stat = "Sum", label = "Errores Tagger", id = "e5", color = "#9467bd" }]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Tasas de error de los agentes"
          period  = 300
          stat    = "Sum"
          yAxis = {
            left = {
              label     = "Cantidad de errores"
              showUnits = false
            }
          }
        }
      },
      # Invocaciones de los agentes
      {
        type   = "metric"
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/Lambda", "Invocations", "FunctionName", "alex-planner", { stat = "Sum", label = "Planner", id = "i1", color = "#1f77b4" }],
            [".", ".", ".", "alex-reporter", { stat = "Sum", label = "Reporter", id = "i2", color = "#2ca02c" }],
            [".", ".", ".", "alex-charter", { stat = "Sum", label = "Charter", id = "i3", color = "#ff7f0e" }],
            [".", ".", ".", "alex-retirement", { stat = "Sum", label = "Retirement", id = "i4", color = "#d62728" }],
            [".", ".", ".", "alex-tagger", { stat = "Sum", label = "Tagger", id = "i5", color = "#9467bd" }]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Conteo de invocaciones de agentes"
          period  = 300
          stat    = "Sum"
          yAxis = {
            left = {
              label     = "Número de invocaciones"
              showUnits = false
            }
          }
        }
      },
      # Ejecuciones concurrentes
      {
        type   = "metric"
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/Lambda", "ConcurrentExecutions", "FunctionName", "alex-planner", { stat = "Maximum", label = "Planner", id = "c1", color = "#1f77b4" }],
            [".", ".", ".", "alex-reporter", { stat = "Maximum", label = "Reporter", id = "c2", color = "#2ca02c" }],
            [".", ".", ".", "alex-charter", { stat = "Maximum", label = "Charter", id = "c3", color = "#ff7f0e" }],
            [".", ".", ".", "alex-retirement", { stat = "Maximum", label = "Retirement", id = "c4", color = "#d62728" }],
            [".", ".", ".", "alex-tagger", { stat = "Maximum", label = "Tagger", id = "c5", color = "#9467bd" }]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Ejecuciones concurrentes"
          period  = 300
          stat    = "Maximum"
          yAxis = {
            left = {
              label     = "Ejecuciones concurrentes"
              showUnits = false
            }
          }
        }
      },
      # Límites (Throttles)
      {
        type   = "metric"
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/Lambda", "Throttles", "FunctionName", "alex-planner", { stat = "Sum", label = "Throttles Planner", id = "t1", color = "#1f77b4" }],
            [".", ".", ".", "alex-reporter", { stat = "Sum", label = "Throttles Reporter", id = "t2", color = "#2ca02c" }],
            [".", ".", ".", "alex-charter", { stat = "Sum", label = "Throttles Charter", id = "t3", color = "#ff7f0e" }],
            [".", ".", ".", "alex-retirement", { stat = "Sum", label = "Throttles Retirement", id = "t4", color = "#d62728" }],
            [".", ".", ".", "alex-tagger", { stat = "Sum", label = "Throttles Tagger", id = "t5", color = "#9467bd" }]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Limitaciones de los agentes"
          period  = 300
          stat    = "Sum"
          yAxis = {
            left = {
              label     = "Cantidad de restricciones"
              showUnits = false
            }
          }
        }
      }
    ]
  })

}
