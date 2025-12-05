# Kubernetes Module Outputs

output "namespace" {
  description = "Kubernetes namespace"
  value       = kubernetes_namespace.vaspnestagent.metadata[0].name
}

output "backend_service_name" {
  description = "Backend service name"
  value       = kubernetes_service.backend.metadata[0].name
}

output "frontend_service_name" {
  description = "Frontend service name"
  value       = kubernetes_service.frontend.metadata[0].name
}

output "ingress_name" {
  description = "Ingress name"
  value       = kubernetes_ingress_v1.main.metadata[0].name
}

output "config_map_name" {
  description = "ConfigMap name"
  value       = kubernetes_config_map.vaspnestagent.metadata[0].name
}

output "service_account_name" {
  description = "Service account name"
  value       = kubernetes_service_account.vaspnestagent.metadata[0].name
}
