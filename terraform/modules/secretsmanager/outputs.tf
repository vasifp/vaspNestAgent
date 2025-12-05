# Secrets Module Outputs

output "nest_credentials_secret_arn" {
  description = "ARN of Nest credentials secret"
  value       = aws_secretsmanager_secret.nest_credentials.arn
}

output "google_voice_secret_arn" {
  description = "ARN of Google Voice credentials secret"
  value       = aws_secretsmanager_secret.google_voice.arn
}

output "secrets_access_policy_arn" {
  description = "ARN of IAM policy for secrets access"
  value       = aws_iam_policy.secrets_access.arn
}
