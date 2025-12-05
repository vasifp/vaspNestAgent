# CloudWatch Module for vaspNestAgent
# Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "main" {
  name              = var.log_group_name
  retention_in_days = var.log_retention_days

  tags = var.tags
}

# CloudWatch Log Stream
resource "aws_cloudwatch_log_stream" "agent" {
  name           = "agent"
  log_group_name = aws_cloudwatch_log_group.main.name
}
