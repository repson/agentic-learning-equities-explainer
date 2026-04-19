variable "aws_region" {
  description = "Región de AWS para los recursos"
  type        = string
}

variable "openai_api_key" {
  description = "Clave API de OpenAI para el agente researcher"
  type        = string
  sensitive   = true
}

variable "alex_api_endpoint" {
  description = "Endpoint de la API de Alex desde la Parte 3"
  type        = string
}

variable "alex_api_key" {
  description = "Clave API de Alex desde la Parte 3"
  type        = string
  sensitive   = true
}

variable "scheduler_enabled" {
  description = "Habilitar programador automático de investigación"
  type        = bool
  default     = false
}