output "dashboard_urls" {
  description = "URLs para acceder a los dashboards de CloudWatch"
  value = {
    ai_model_usage    = "https://console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.ai_model_usage.dashboard_name}"
    agent_performance = "https://console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.agent_performance.dashboard_name}"
  }
}

output "dashboard_names" {
  description = "Nombres de los dashboards creados"
  value = {
    ai_model_usage    = aws_cloudwatch_dashboard.ai_model_usage.dashboard_name
    agent_performance = aws_cloudwatch_dashboard.agent_performance.dashboard_name
  }
}

output "setup_instructions" {
  description = "Instrucciones para usar los dashboards"
  value = <<-EOT

    ✅ ¡Dashboards de CloudWatch desplegados correctamente!

    Dashboards creados:
    - Dashboard de Uso de Modelos de IA: ${aws_cloudwatch_dashboard.ai_model_usage.dashboard_name}
    - Dashboard de Rendimiento de Agentes: ${aws_cloudwatch_dashboard.agent_performance.dashboard_name}

    Para ver los dashboards:
    1. Inicia sesión en la consola de AWS
    2. Navega hasta CloudWatch → Dashboards
    3. Selecciona tu dashboard de la lista

    O utiliza estos enlaces directos:
    - Uso de Modelos de IA: https://console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.ai_model_usage.dashboard_name}
    - Rendimiento de Agentes: https://console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.agent_performance.dashboard_name}

    Características de los dashboards:

    Dashboard de Uso de Modelos de IA:
    - Invocaciones y errores de modelos Bedrock
    - Seguimiento del uso de tokens (input/output)
    - Métricas de latencia de respuesta del modelo
    - Invocaciones a endpoints SageMaker
    - Latencia de modelos SageMaker
    - Utilización de recursos del endpoint (CPU/Memoria)

    Dashboard de Rendimiento de Agentes:
    - Tiempos de ejecución para cada agente
    - Conteo de invocaciones por agente
    - Monitorización de tasas de error
    - Total de invocaciones en el tiempo
    - Métricas de ejecución concurrente
    - Detección de throttling

    Nota: Algunas métricas pueden tardar algunos minutos en aparecer tras el despliegue inicial.
    Asegúrate de que tus funciones Lambda se han invocado al menos una vez para ver datos.
  EOT
}