# CloudWatch Module Outputs

output "log_group_name" {
  description = "CloudWatch log group name"
  value       = aws_cloudwatch_log_group.main.name
}

output "log_group_arn" {
  description = "CloudWatch log group ARN"
  value       = aws_cloudwatch_log_group.main.arn
}

output "dashboard_name" {
  description = "CloudWatch dashboard name"
  value       = aws_cloudwatch_dashboard.main.dashboard_name
}

output "dashboard_arn" {
  description = "CloudWatch dashboard ARN"
  value       = aws_cloudwatch_dashboard.main.dashboard_arn
}

output "high_error_alarm_arn" {
  description = "High error rate alarm ARN"
  value       = aws_cloudwatch_metric_alarm.high_error_rate.arn
}

output "unhealthy_alarm_arn" {
  description = "Unhealthy agent alarm ARN"
  value       = aws_cloudwatch_metric_alarm.agent_unhealthy.arn
}
