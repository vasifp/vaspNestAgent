# Secrets Manager Module for vaspNestAgent
# Requirements: 4.7, 3.6

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Nest API Credentials Secret
resource "aws_secretsmanager_secret" "nest_credentials" {
  name        = "vaspnestagent/nest-credentials"
  description = "Google Nest API credentials for vaspNestAgent"

  tags = var.tags
}

resource "aws_secretsmanager_secret_version" "nest_credentials" {
  secret_id = aws_secretsmanager_secret.nest_credentials.id
  secret_string = jsonencode({
    client_id     = var.nest_client_id
    client_secret = var.nest_client_secret
    refresh_token = var.nest_refresh_token
    project_id    = var.nest_project_id
  })
}

# Google Voice Credentials Secret
resource "aws_secretsmanager_secret" "google_voice" {
  name        = "vaspnestagent/google-voice"
  description = "Google Voice credentials for vaspNestAgent notifications"

  tags = var.tags
}

resource "aws_secretsmanager_secret_version" "google_voice" {
  secret_id = aws_secretsmanager_secret.google_voice.id
  secret_string = jsonencode({
    credentials  = var.google_voice_credentials
    phone_number = var.google_voice_phone_number
  })
}

# IAM Policy for accessing secrets
resource "aws_iam_policy" "secrets_access" {
  name        = "vaspnestagent-secrets-access"
  description = "Policy for accessing vaspNestAgent secrets"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = [
          aws_secretsmanager_secret.nest_credentials.arn,
          aws_secretsmanager_secret.google_voice.arn
        ]
      }
    ]
  })

  tags = var.tags
}
