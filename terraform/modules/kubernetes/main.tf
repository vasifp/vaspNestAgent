# Kubernetes Module for vaspNestAgent
# Requirements: 4.8, 17.5

terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
  }
}

# Namespace
resource "kubernetes_namespace" "vaspnestagent" {
  metadata {
    name = var.namespace
    labels = {
      app = "vaspnestagent"
    }
  }
}

# ConfigMap
resource "kubernetes_config_map" "vaspnestagent" {
  metadata {
    name      = "vaspnestagent-config"
    namespace = kubernetes_namespace.vaspnestagent.metadata[0].name
  }

  data = {
    POLLING_INTERVAL                = tostring(var.polling_interval)
    COOLDOWN_PERIOD                 = tostring(var.cooldown_period)
    TEMPERATURE_THRESHOLD           = tostring(var.temperature_threshold)
    TEMPERATURE_ADJUSTMENT          = tostring(var.temperature_adjustment)
    CLOUDWATCH_LOG_GROUP            = var.cloudwatch_log_group
    AWS_REGION                      = var.aws_region
    HTTP_PORT                       = tostring(var.http_port)
    ERROR_THRESHOLD                 = tostring(var.error_threshold)
    NOTIFICATION_RATE_LIMIT_ENABLED = tostring(var.notification_rate_limit_enabled)
    NOTIFICATION_RATE_LIMIT_SECONDS = tostring(var.notification_rate_limit_seconds)
  }
}

# Service Account
resource "kubernetes_service_account" "vaspnestagent" {
  metadata {
    name      = "vaspnestagent"
    namespace = kubernetes_namespace.vaspnestagent.metadata[0].name
    annotations = {
      "eks.amazonaws.com/role-arn" = var.service_account_role_arn
    }
  }
}
