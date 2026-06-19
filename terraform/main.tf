terraform {
  required_version = ">= 1.5.0"
}

locals {
  deployment_name = "${var.project_name}-${var.environment}"
  common_tags = {
    project     = var.project_name
    environment = var.environment
    managed_by  = "terraform"
    demo_ready  = "true"
  }
}

resource "terraform_data" "network" {
  input = {
    name   = "${local.deployment_name}-network"
    driver = "bridge"
    tags   = local.common_tags
  }
}

resource "terraform_data" "app_service" {
  input = {
    name         = "${local.deployment_name}-app"
    image        = var.app_image_name
    exposed_port = var.app_port
    network      = terraform_data.network.output.name
    tags         = local.common_tags
  }
}

resource "terraform_data" "proxy_service" {
  input = {
    name         = "${local.deployment_name}-proxy"
    image        = var.proxy_image_name
    exposed_port = var.proxy_port
    network      = terraform_data.network.output.name
    tags         = local.common_tags
  }
}

resource "terraform_data" "deployment_target" {
  input = {
    project_name       = var.project_name
    environment        = var.environment
    deployment_target  = var.deployment_target
    provisioned_status = "ready"
    app_service_name   = terraform_data.app_service.output.name
    proxy_service_name = terraform_data.proxy_service.output.name
  }
}
