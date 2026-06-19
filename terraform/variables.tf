variable "project_name" {
  description = "Project name shown in Terraform plan and outputs."
  type        = string
  default     = "sentinelci"
}

variable "environment" {
  description = "Environment label for the demo infrastructure."
  type        = string
  default     = "demo"
}

variable "deployment_target" {
  description = "Where the demo stack is intended to run."
  type        = string
  default     = "docker-host"
}

variable "app_image_name" {
  description = "Application container image name."
  type        = string
  default     = "sentinelci-app:latest"
}

variable "proxy_image_name" {
  description = "Reverse proxy container image name."
  type        = string
  default     = "sentinelci-proxy:latest"
}

variable "app_port" {
  description = "FastAPI container port."
  type        = number
  default     = 8000
}

variable "proxy_port" {
  description = "Proxy container port exposed to users."
  type        = number
  default     = 8080
}
