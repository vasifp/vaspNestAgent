# CloudWatch Module Variables

variable "log_group_name" {
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

variable "aws_region" {
  description = "AWS region for metrics"
  type        = string
  default     = "us-east-1"
}

variable "error_alarm_threshold" {
  description = "Error count threshold for alarm"
  type        = number
  default     = 10
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
