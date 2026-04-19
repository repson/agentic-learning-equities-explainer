output "aurora_cluster_arn" {
  description = "ARN del clúster Aurora"
  value       = aws_rds_cluster.aurora.arn
}

output "aurora_cluster_endpoint" {
  description = "Endpoint de escritura del clúster Aurora"
  value       = aws_rds_cluster.aurora.endpoint
}

output "aurora_secret_arn" {
  description = "ARN del secreto en Secrets Manager que contiene las credenciales de la base de datos"
  value       = aws_secretsmanager_secret.db_credentials.arn
}

output "database_name" {
  description = "Nombre de la base de datos"
  value       = aws_rds_cluster.aurora.database_name
}

output "lambda_role_arn" {
  description = "ARN del rol IAM para Lambdas con acceso a Aurora"
  value       = aws_iam_role.lambda_aurora_role.arn
}

output "data_api_enabled" {
  description = "Estado de la Data API"
  value       = aws_rds_cluster.aurora.enable_http_endpoint ? "Habilitada" : "Deshabilitada"
}

output "setup_instructions" {
  description = "Instrucciones para configurar la base de datos"
  value = <<-EOT
    
    ✅ ¡Clúster Aurora Serverless v2 desplegado con éxito!
    
    Detalles de la base de datos:
    - Clúster: ${aws_rds_cluster.aurora.cluster_identifier}
    - Base de datos: ${aws_rds_cluster.aurora.database_name}
    - Data API: Habilitada
    
    Añade lo siguiente a tu archivo .env:
    AURORA_CLUSTER_ARN=${aws_rds_cluster.aurora.arn}
    AURORA_SECRET_ARN=${aws_secretsmanager_secret.db_credentials.arn}
    
    Prueba la conexión Data API:
    aws rds-data execute-statement \
      --resource-arn ${aws_rds_cluster.aurora.arn} \
      --secret-arn ${aws_secretsmanager_secret.db_credentials.arn} \
      --database alex \
      --sql "SELECT version()"
    
    Para crear el esquema de la base de datos:
    cd backend/database
    uv run migrate.py
    
    Para cargar datos de ejemplo:
    uv run reset_db.py --with-test-data
    
    💰 Gestión de costes:
    - Escalado actual: ${var.min_capacity} - ${var.max_capacity} ACUs
    - Coste estimado: ~$43/mes mínimo
    - Para pausar: Establece min_capacity a 0 (el clúster se pausará tras 5 minutos de inactividad)
  EOT
}