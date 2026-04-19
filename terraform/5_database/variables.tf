variable "aws_region" {
  description = "Región de AWS para los recursos"
  type        = string
}

variable "min_capacity" {
  description = "Capacidad mínima para Aurora Serverless v2 (en ACUs)"
  type        = number
  default     = 0.5
}

variable "max_capacity" {
  description = "Capacidad máxima para Aurora Serverless v2 (en ACUs)"
  type        = number
  default     = 1
}