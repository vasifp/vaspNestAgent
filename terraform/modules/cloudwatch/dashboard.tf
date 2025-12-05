# CloudWatch Dashboard for vaspNestAgent
# Requirements: 12.2, 12.3, 12.4, 12.5, 12.6

resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = var.dashboard_name

  dashboard_body = jsonencode({
    widgets = [
      # Temperature Readings Widget
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "Temperature Readings"
          region = var.aws_region
          metrics = [
            ["vaspNestAgent", "AmbientTemperature", { label = "Ambient (°F)" }],
            ["vaspNestAgent", "TargetTemperature", { label = "Target (°F)" }]
          ]
          period = 60
          stat   = "Average"
          view   = "timeSeries"
          yAxis = {
            left = {
              min = 50
              max = 90
            }
          }
        }
      },
      # Adjustment Counts Widget
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "Temperature Adjustments"
          region = var.aws_region
          metrics = [
            ["vaspNestAgent", "AdjustmentCount", { stat = "Sum", label = "Adjustments" }]
          ]
          period = 3600
          view   = "timeSeries"
        }
      },
      # Notification Status Widget
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        properties = {
          title  = "Notification Status"
          region = var.aws_region
          metrics = [
            ["vaspNestAgent", "NotificationSuccess", { stat = "Sum", label = "Sent" }],
            ["vaspNestAgent", "NotificationFailure", { stat = "Sum", label = "Failed" }],
            ["vaspNestAgent", "NotificationSuppressed", { stat = "Sum", label = "Rate Limited" }]
          ]
          period = 3600
          view   = "timeSeries"
        }
      },
      # API Latencies Widget
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6
        properties = {
          title  = "API Latencies"
          region = var.aws_region
          metrics = [
            ["vaspNestAgent", "NestAPILatency", { stat = "Average", label = "Nest API (ms)" }],
            ["vaspNestAgent", "GoogleVoiceLatency", { stat = "Average", label = "Google Voice (ms)" }]
          ]
          period = 300
          view   = "timeSeries"
        }
      },
      # Error Counts Widget
      {
        type   = "metric"
        x      = 0
        y      = 12
        width  = 12
        height = 6
        properties = {
          title  = "Error Counts"
          region = var.aws_region
          metrics = [
            ["vaspNestAgent", "ErrorCount", { stat = "Sum", label = "Total Errors" }],
            ["vaspNestAgent", "ConsecutiveErrors", { stat = "Maximum", label = "Consecutive" }]
          ]
          period = 300
          view   = "timeSeries"
        }
      },
      # Health Status Widget
      {
        type   = "metric"
        x      = 12
        y      = 12
        width  = 12
        height = 6
        properties = {
          title  = "Health Status"
          region = var.aws_region
          metrics = [
            ["vaspNestAgent", "HealthStatus", { stat = "Minimum", label = "Health (1=OK)" }],
            ["vaspNestAgent", "Uptime", { stat = "Maximum", label = "Uptime (s)" }]
          ]
          period = 60
          view   = "timeSeries"
        }
      },
      # Temperature Differential Widget
      {
        type   = "metric"
        x      = 0
        y      = 18
        width  = 24
        height = 6
        properties = {
          title  = "Temperature Differential (Target - Ambient)"
          region = var.aws_region
          metrics = [
            ["vaspNestAgent", "TemperatureDifferential", { stat = "Average", label = "Differential (°F)" }]
          ]
          period = 60
          view   = "timeSeries"
          annotations = {
            horizontal = [
              {
                label = "Adjustment Threshold"
                value = 5
                color = "#ff7f0e"
              }
            ]
          }
        }
      }
    ]
  })
}

# CloudWatch Alarms
resource "aws_cloudwatch_metric_alarm" "high_error_rate" {
  alarm_name          = "${var.dashboard_name}-high-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ErrorCount"
  namespace           = "vaspNestAgent"
  period              = 300
  statistic           = "Sum"
  threshold           = var.error_alarm_threshold
  alarm_description   = "High error rate detected in vaspNestAgent"
  treat_missing_data  = "notBreaching"

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "agent_unhealthy" {
  alarm_name          = "${var.dashboard_name}-unhealthy"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 3
  metric_name         = "HealthStatus"
  namespace           = "vaspNestAgent"
  period              = 60
  statistic           = "Minimum"
  threshold           = 1
  alarm_description   = "vaspNestAgent is unhealthy"
  treat_missing_data  = "breaching"

  tags = var.tags
}
