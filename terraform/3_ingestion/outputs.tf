output "vector_bucket_name" {
  description = "Nombre del bucket de S3 Vectors"
  value       = aws_s3_bucket.vectors.id
}

output "api_endpoint" {
  description = "URL del endpoint de API Gateway"
  value       = "${aws_api_gateway_stage.api.invoke_url}/ingest"
}

output "api_key_id" {
  description = "ID de la API Key"
  value       = aws_api_gateway_api_key.api_key.id
}

output "api_key_value" {
  description = "Valor de la API Key (sensible)"
  value       = aws_api_gateway_api_key.api_key.value
  sensitive   = true
}

output "setup_instructions" {
  description = "Instrucciones para configurar las variables de entorno"
  value = <<-EOT

    ✅ ¡Pipeline de ingesta desplegado con éxito!

    Añade lo siguiente a tu archivo .env:
    VECTOR_BUCKET=${aws_s3_bucket.vectors.id}
    ALEX_API_ENDPOINT=${aws_api_gateway_stage.api.invoke_url}/ingest

    Para obtener el valor de tu API key:
    aws apigateway get-api-key --api-key ${aws_api_gateway_api_key.api_key.id} --include-value --query 'value' --output text

    Luego añade en .env:
    ALEX_API_KEY=<el-valor-de-tu-api-key>

    Prueba la API:
    curl -X POST ${aws_api_gateway_stage.api.invoke_url}/ingest \
      -H "x-api-key: <tu-api-key>" \
      -H "Content-Type: application/json" \
      -d '{"content": "Documento de prueba", "metadata": {"source": "test"}}'
  EOT
}