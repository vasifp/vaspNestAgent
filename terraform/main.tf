# Main Terraform Configuration for vaspNestAgent
# Requirements: 8.1

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "vaspNestAgent"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# VPC Module
module "vpc" {
  source = "./modules/vpc"

  project_name         = var.project_name
  cluster_name         = var.cluster_name
  vpc_cidr             = var.vpc_cidr
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
  availability_zones   = var.availability_zones

  tags = local.tags
}

# EKS Module
module "eks" {
  source = "./modules/eks"

  cluster_name        = var.cluster_name
  cluster_version     = var.cluster_version
  vpc_id              = module.vpc.vpc_id
  subnet_ids          = module.vpc.private_subnet_ids
  node_desired_size   = var.node_desired_size
  node_max_size       = var.node_max_size
  node_min_size       = var.node_min_size
  node_instance_types = var.node_instance_types

  tags = local.tags
}

# ECR Module
module "ecr" {
  source = "./modules/ecr"

  project_name        = var.project_name
  image_count_to_keep = var.ecr_image_count_to_keep

  tags = local.tags
}

# Secrets Manager Module
module "secretsmanager" {
  source = "./modules/secretsmanager"

  nest_client_id            = var.nest_client_id
  nest_client_secret        = var.nest_client_secret
  nest_refresh_token        = var.nest_refresh_token
  nest_project_id           = var.nest_project_id
  google_voice_credentials  = var.google_voice_credentials
  google_voice_phone_number = var.google_voice_phone_number

  tags = local.tags
}

# CloudWatch Module
module "cloudwatch" {
  source = "./modules/cloudwatch"

  log_group_name        = var.cloudwatch_log_group
  log_retention_days    = var.log_retention_days
  dashboard_name        = var.dashboard_name
  aws_region            = var.aws_region
  error_alarm_threshold = var.error_threshold

  tags = local.tags
}

# Kubernetes Provider Configuration
provider "kubernetes" {
  host                   = module.eks.cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)

  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "aws"
    args        = ["eks", "get-token", "--cluster-name", module.eks.cluster_name]
  }
}

# Kubernetes Module
module "kubernetes" {
  source = "./modules/kubernetes"

  namespace                = var.kubernetes_namespace
  service_account_role_arn = module.eks.node_role_arn

  backend_image     = module.ecr.backend_repository_url
  backend_image_tag = var.backend_image_tag
  backend_replicas  = var.backend_replicas

  frontend_image     = module.ecr.frontend_repository_url
  frontend_image_tag = var.frontend_image_tag
  frontend_replicas  = var.frontend_replicas

  polling_interval                = var.polling_interval
  cooldown_period                 = var.cooldown_period
  temperature_threshold           = var.temperature_threshold
  temperature_adjustment          = var.temperature_adjustment
  cloudwatch_log_group            = var.cloudwatch_log_group
  aws_region                      = var.aws_region
  error_threshold                 = var.error_threshold
  notification_rate_limit_enabled = var.notification_rate_limit_enabled
  notification_rate_limit_seconds = var.notification_rate_limit_seconds

  depends_on = [module.eks]
}

# Local values
locals {
  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}
