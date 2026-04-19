variable "aws_region" {
  description = "Región AWS para los recursos"
  type        = string
}

variable "sagemaker_image_uri" {
  description = "URI de la imagen de contenedor de SageMaker"
  type        = string
  default     = "763104351884.dkr.ecr.us-east-1.amazonaws.com/huggingface-pytorch-inference:1.13.1-transformers4.26.0-cpu-py39-ubuntu20.04"
}

variable "embedding_model_name" {
  description = "Nombre del modelo HuggingFace a utilizar"
  type        = string
  default     = "sentence-transformers/all-MiniLM-L6-v2"
}