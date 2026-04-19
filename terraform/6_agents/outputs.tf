output "sqs_queue_url" {
  description = "URL de la cola SQS para envío de trabajos"
  value       = aws_sqs_queue.analysis_jobs.url
}

output "sqs_queue_arn" {
  description = "ARN de la cola SQS"
  value       = aws_sqs_queue.analysis_jobs.arn
}

output "lambda_functions" {
  description = "Nombres de las funciones Lambda desplegadas"
  value = {
    planner    = aws_lambda_function.planner.function_name
    tagger     = aws_lambda_function.tagger.function_name
    reporter   = aws_lambda_function.reporter.function_name
    charter    = aws_lambda_function.charter.function_name
    retirement = aws_lambda_function.retirement.function_name
  }
}

output "setup_instructions" {
  description = "Instrucciones para probar los agentes"
  value = <<-EOT
    
    ✅ ¡Infraestructura de agentes desplegada correctamente!
    
    Funciones Lambda:
    - Planner (Orquestador): ${aws_lambda_function.planner.function_name}
    - Tagger: ${aws_lambda_function.tagger.function_name}
    - Reporter: ${aws_lambda_function.reporter.function_name}
    - Charter: ${aws_lambda_function.charter.function_name}
    - Retirement: ${aws_lambda_function.retirement.function_name}
    
    Cola SQS: ${aws_sqs_queue.analysis_jobs.name}
    
    Para probar el sistema:
    1. Primero, empaqueta y despliega el código de cada agente:
       cd backend/planner && uv run package_docker.py --deploy
       cd backend/tagger && uv run package_docker.py --deploy
       cd backend/reporter && uv run package_docker.py --deploy
       cd backend/charter && uv run package_docker.py --deploy
       cd backend/retirement && uv run package_docker.py --deploy
    
    2. Ejecuta la prueba de integración completa:
       cd backend/planner
       uv run run_full_test.py
    
    3. Supervisa el progreso en los logs de CloudWatch:
       - /aws/lambda/alex-planner
       - /aws/lambda/alex-tagger
       - /aws/lambda/alex-reporter
       - /aws/lambda/alex-charter
       - /aws/lambda/alex-retirement
    
    Modelo Bedrock: ${var.bedrock_model_id}
    Región: ${var.bedrock_region}
  EOT
}