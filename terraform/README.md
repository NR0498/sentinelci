# Terraform Demo

This Terraform configuration is a safe local Infrastructure as Code demo for SentinelCI.

It does not require AWS or any other cloud credentials.
Instead, it uses Terraform's built-in `terraform_data` resource to simulate:

- a deployment network
- an application service
- a reverse proxy service
- a deployment target summary

## Files

- `main.tf`: simulated infrastructure resources
- `variables.tf`: input variables for the demo
- `outputs.tf`: screenshot-friendly Terraform outputs

## Commands

Initialize Terraform:

```bash
terraform init
```

Validate configuration:

```bash
terraform validate
```

Generate a plan:

```bash
terraform plan
```

Apply the demo configuration:

```bash
terraform apply -auto-approve
```

Show outputs:

```bash
terraform output
```

## Expected Screenshot Outputs

After `terraform apply`, the most useful outputs are:

- `project_name`
- `environment`
- `provisioned_status`
- `docker_image_name`
- `proxy_image_name`
- `deployment_target`
- `network_name`
- `service_summary`

## Optional Cloud Note

If you want to extend this into AWS later, keep the current local demo as the default and add any cloud resources as a separate optional configuration so screenshots stay reliable without credentials.
