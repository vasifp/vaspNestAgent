# Terraform Variables for vaspNestAgent
# Requirements: 8.2

# General
variable "project_name" {
  description = "Project name"
  type        = string
  default     = "vaspnestagent"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# VPC Configuration
variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "Public subnet CIDR blocks"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "Private subnet CIDR blocks"
  type        = list(string)
  default     = ["10.0.10.0/24", "10.0.20.0/24"]
}

variable "availability_zones" {
  description = "Availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

# EKS Configuration
variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
  default     = "vaspnestagent-cluster"
}

variable "cluster_version" {
  description = "Kubernetes version (1.31 or higher recommended)"
  type        = string
  default     = "1.31"
}

variable "node_desired_size" {
  description = "Desired number of worker nodes"
  type        = number
  default     = 2
}

variable "node_max_size" {
  description = "Maximum number of worker nodes"
  type        = number
  default     = 4
}

variable "node_min_size" {
  description = "Minimum number of worker nodes"
  type        = number
  default     = 1
}

variable "node_instance_types" {
  description = "Instance types for worker nodes"
  type        = list(string)
  default     = ["t3.medium"]
}

# ECR Configuration
variable "ecr_image_count_to_keep" {
  description = "Number of images to keep in ECR"
  type        = number
  default     = 10
}

# Secrets (sensitive)
variable "nest_client_id" {
  description = "Google Nest OAuth client ID"
  type        = string
  sensitive   = true
}

variable "nest_client_secret" {
  description = "Google Nest OAuth client secret"
  type        = string
  sensitive   = true
}

variable "nest_refresh_token" {
  description = "Google Nest OAuth refresh token"
  type        = string
  sensitive   = true
}

variable "nest_project_id" {
  description = "Google Nest project ID"
  type        = string
  sensitive   = true
}

variable "google_voice_credentials" {
  description = "Google Voice API credentials"
  type        = string
  sensitive   = true
}

variable "google_voice_phone_number" {
  description = "Google Voice phone number for notifications"
  type        = string
  sensitive   = true
  default     = "480-442-0574"
}

# CloudWatch Configuration
variable "cloudwatch_log_group" {
  description = "CloudWatch log group name"
  type        = string
  default     = "/vaspNestAgent/logs"
}

variable "log_retention_days" {
  description = "Log retention period in days"
  type        = number
  default     = 30
}

variable "dashboard_name" {
  description = "CloudWatch dashboard name"
  type        = string
  default     = "vaspNestAgent"
}

# Kubernetes Configuration
variable "kubernetes_namespace" {
  description = "Kubernetes namespace"
  type        = string
  default     = "vaspnestagent"
}

variable "backend_image_tag" {
  description = "Backend Docker image tag"
  type        = string
  default     = "latest"
}

variable "backend_replicas" {
  description = "Number of backend replicas"
  type        = number
  default     = 1
}

variable "frontend_image_tag" {
  description = "Frontend Docker image tag"
  type        = string
  default     = "latest"
}

variable "frontend_replicas" {
  description = "Number of frontend replicas"
  type        = number
  default     = 2
}

# Application Configuration
variable "polling_interval" {
  description = "Temperature polling interval in seconds"
  type        = number
  default     = 60
}

variable "cooldown_period" {
  description = "Cooldown period after adjustment in seconds"
  type        = number
  default     = 1800
}

variable "temperature_threshold" {
  description = "Temperature differential threshold (°F)"
  type        = number
  default     = 5
}

variable "temperature_adjustment" {
  description = "Temperature adjustment amount (°F)"
  type        = number
  default     = 5
}

variable "error_threshold" {
  description = "Error threshold for alerting"
  type        = number
  default     = 10
}

variable "notification_rate_limit_enabled" {
  description = "Enable notification rate limiting"
  type        = bool
  default     = true
}

variable "notification_rate_limit_seconds" {
  description = "Notification rate limit window in seconds"
  type        = number
  default     = 3600
}
