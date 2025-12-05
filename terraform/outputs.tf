# Terraform Outputs for vaspNestAgent
# Requirements: 8.4

# VPC Outputs
output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = module.vpc.public_subnet_ids
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = module.vpc.private_subnet_ids
}

# EKS Outputs
output "eks_cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.eks.cluster_endpoint
}

output "eks_kubeconfig_command" {
  description = "Command to update kubeconfig"
  value       = module.eks.kubeconfig_command
}

# ECR Outputs
output "ecr_backend_repository_url" {
  description = "Backend ECR repository URL"
  value       = module.ecr.backend_repository_url
}

output "ecr_frontend_repository_url" {
  description = "Frontend ECR repository URL"
  value       = module.ecr.frontend_repository_url
}

# CloudWatch Outputs
output "cloudwatch_log_group" {
  description = "CloudWatch log group name"
  value       = module.cloudwatch.log_group_name
}

output "cloudwatch_dashboard_name" {
  description = "CloudWatch dashboard name"
  value       = module.cloudwatch.dashboard_name
}

# Kubernetes Outputs
output "kubernetes_namespace" {
  description = "Kubernetes namespace"
  value       = module.kubernetes.namespace
}

# Deployment Commands
output "docker_login_command" {
  description = "Command to login to ECR"
  value       = "aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${module.ecr.backend_repository_url}"
}

output "backend_push_commands" {
  description = "Commands to build and push backend image"
  value       = <<-EOT
    docker build -t ${module.ecr.backend_repository_url}:latest .
    docker push ${module.ecr.backend_repository_url}:latest
  EOT
}

output "frontend_push_commands" {
  description = "Commands to build and push frontend image"
  value       = <<-EOT
    docker build -t ${module.ecr.frontend_repository_url}:latest ./frontend
    docker push ${module.ecr.frontend_repository_url}:latest
  EOT
}
