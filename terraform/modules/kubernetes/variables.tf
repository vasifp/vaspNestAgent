# Kubernetes Module Variables

variable "namespace" {
  description = "Kubernetes namespace"
  type        = string
  default     = "vaspnestagent"
}

variable "service_account_role_arn" {
  description = "IAM role ARN for service account"
  type        = string
}

# Backend Configuration
variable "backend_image" {
  description = "Backend Docker image"
  type        = string
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

variable "backend_memory_request" {
  description = "Backend memory request"
  type        = string
  default     = "256Mi"
}

variable "backend_memory_limit" {
  description = "Backend memory limit"
  type        = string
  default     = "512Mi"
}

variable "backend_cpu_request" {
  description = "Backend CPU request"
  type        = string
  default     = "100m"
}

variable "backend_cpu_limit" {
  description = "Backend CPU limit"
  type        = string
  default     = "500m"
}

# Frontend Configuration
variable "frontend_image" {
  description = "Frontend Docker image"
  type        = string
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

variable "frontend_memory_request" {
  description = "Frontend memory request"
  type        = string
  default     = "64Mi"
}

variable "frontend_memory_limit" {
  description = "Frontend memory limit"
  type        = string
  default     = "128Mi"
}

variable "frontend_cpu_request" {
  description = "Frontend CPU request"
  type        = string
  default     = "50m"
}

variable "frontend_cpu_limit" {
  description = "Frontend CPU limit"
  type        = string
  default     = "200m"
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
  description = "Temperature differential threshold"
  type        = number
  default     = 5
}

variable "temperature_adjustment" {
  description = "Temperature adjustment amount"
  type        = number
  default     = 5
}

variable "cloudwatch_log_group" {
  description = "CloudWatch log group name"
  type        = string
  default     = "/vaspNestAgent/logs"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "http_port" {
  description = "HTTP port for backend"
  type        = number
  default     = 8080
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
