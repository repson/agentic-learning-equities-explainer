output "ecr_repository_url" {
  description = "URL del repositorio ECR"
  value       = aws_ecr_repository.researcher.repository_url
}

output "app_runner_service_url" {
  description = "URL del servicio App Runner"
  value       = try("https://${aws_apprunner_service.researcher.service_url}", "Aún no creado - ejecuta 'terraform apply' después de desplegar la imagen Docker")
}

output "app_runner_service_id" {
  description = "ID del servicio App Runner"
  value       = try(aws_apprunner_service.researcher.id, "Aún no creado")
}

output "scheduler_status" {
  description = "Estado del programador automático"
  value       = var.scheduler_enabled ? "Activado - Ejecutándose cada 2 horas" : "Desactivado"
}

output "setup_instructions" {
  description = "Instrucciones para completar la configuración"
  value = <<-EOT
    
    ✅ ¡Servicio Researcher desplegado con éxito!
    
    URL del servicio: https://${aws_apprunner_service.researcher.service_url}
    
    Prueba el researcher:
    curl https://${aws_apprunner_service.researcher.service_url}/research
    
    ${var.scheduler_enabled ? "⏰ La investigación automática se ejecuta cada 2 horas" : "💡 Para activar la investigación automática, pon scheduler_enabled = true"}
    
    Nota: Debes desplegar tu código real de researcher en App Runner.
    Sigue la guía para instrucciones sobre cómo construir y desplegar la imagen Docker.
  EOT
}