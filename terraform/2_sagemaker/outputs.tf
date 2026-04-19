
output "sagemaker_endpoint_name" {
  description = "Nombre del endpoint de SageMaker"
  value       = aws_sagemaker_endpoint.embedding_endpoint.name
}

output "sagemaker_endpoint_arn" {
  description = "ARN del endpoint de SageMaker"
  value       = aws_sagemaker_endpoint.embedding_endpoint.arn
}

output "setup_instructions" {
  description = "Instrucciones para configurar las variables de entorno"
  value = <<-EOT
    
    ✅ ¡Endpoint de SageMaker desplegado con éxito!
    
    Sigue las instrucciones de la guía para actualizar tu archivo .env y probar el endpoint.
  EOT
}