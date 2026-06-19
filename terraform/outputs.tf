output "project_name" {
  description = "Project name configured for the Terraform demo."
  value       = var.project_name
}

output "environment" {
  description = "Environment label configured for the Terraform demo."
  value       = var.environment
}

output "provisioned_status" {
  description = "Simulated provisioning status for screenshots."
  value       = terraform_data.deployment_target.output.provisioned_status
}

output "docker_image_name" {
  description = "Primary application image configured for deployment."
  value       = terraform_data.app_service.output.image
}

output "proxy_image_name" {
  description = "Reverse proxy image configured for deployment."
  value       = terraform_data.proxy_service.output.image
}

output "deployment_target" {
  description = "Deployment target used by the demo stack."
  value       = terraform_data.deployment_target.output.deployment_target
}

output "network_name" {
  description = "Docker network name provisioned by Terraform."
  value       = terraform_data.network.output.name
}

output "service_summary" {
  description = "Summary of the simulated infrastructure resources."
  value = {
    app_service   = terraform_data.app_service.output.name
    app_port      = terraform_data.app_service.output.exposed_port
    proxy_service = terraform_data.proxy_service.output.name
    proxy_port    = terraform_data.proxy_service.output.exposed_port
  }
}
