output "cloudfront_url" {
  description = "URL de la distribución de CloudFront"
  value       = "https://${aws_cloudfront_distribution.main.domain_name}"
}

output "api_gateway_url" {
  description = "URL de API Gateway"
  value       = aws_apigatewayv2_api.main.api_endpoint
}

output "s3_bucket_name" {
  description = "Nombre del bucket S3 para el frontend"
  value       = aws_s3_bucket.frontend.id
}

output "lambda_function_name" {
  description = "Nombre de la función Lambda de la API"
  value       = aws_lambda_function.api.function_name
}

output "setup_instructions" {
  description = "Instrucciones para completar el despliegue"
  value = <<-EOT

    ✅ ¡Infraestructura de Frontend & API desplegada correctamente!

    URL de CloudFront: https://${aws_cloudfront_distribution.main.domain_name}
    API Gateway: ${aws_apigatewayv2_api.main.api_endpoint}
    S3 Bucket: ${aws_s3_bucket.frontend.id}
    Lambda Function: ${aws_lambda_function.api.function_name}

    Siguientes pasos:

    1. Si desplegaste manualmente (no usando scripts/deploy.py):
       a. Genera y sube el frontend:
          cd frontend
          npm run build
          aws s3 sync out/ s3://${aws_s3_bucket.frontend.id}/ --delete

       b. Invalida la caché de CloudFront:
          aws cloudfront create-invalidation \
            --distribution-id ${aws_cloudfront_distribution.main.id} \
            --paths "/*"

    2. Prueba el despliegue:
       - Visita: https://${aws_cloudfront_distribution.main.domain_name}
       - Inicia sesión con Clerk
       - Revisa las llamadas API en la pestaña Network

    3. Monitorea en la consola AWS:
       - Logs de CloudWatch: /aws/lambda/${aws_lambda_function.api.function_name}
       - Métricas de API Gateway
       - Métricas de CloudFront

    Para destruir: cd scripts && uv run destroy.py
  EOT
}