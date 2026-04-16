terraform {
  required_version = ">= 1.5.0"
}

variable "project_name" {
  description = "Logical name of the service being provisioned."
  type        = string
  default     = "sentinelci"
}

variable "environment" {
  description = "Deployment environment name."
  type        = string
  default     = "dev"
}

variable "container_image" {
  description = "Container image that the target host should run."
  type        = string
  default     = "docker.io/library/sentinelci:latest"
}

variable "service_port" {
  description = "Application port exposed by the container."
  type        = number
  default     = 8000
}

locals {
  deployment_name = "${var.project_name}-${var.environment}"
  tags = {
    project     = var.project_name
    environment = var.environment
    managed_by  = "terraform"
  }
}

resource "terraform_data" "docker_host" {
  input = {
    name            = local.deployment_name
    container_image = var.container_image
    service_port    = var.service_port
    tags            = local.tags
  }
}

output "deployment_summary" {
  description = "Simulated infrastructure details for the SentinelCI Docker host."
  value = {
    host_name       = terraform_data.docker_host.output.name
    container_image = terraform_data.docker_host.output.container_image
    service_port    = terraform_data.docker_host.output.service_port
    tags            = terraform_data.docker_host.output.tags
  }
}
