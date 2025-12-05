# Kubernetes Deployments for vaspNestAgent

# Backend Deployment
resource "kubernetes_deployment" "backend" {
  metadata {
    name      = "vaspnestagent-backend"
    namespace = kubernetes_namespace.vaspnestagent.metadata[0].name
    labels = {
      app = "vaspnestagent-backend"
    }
  }

  spec {
    replicas = var.backend_replicas

    selector {
      match_labels = {
        app = "vaspnestagent-backend"
      }
    }

    template {
      metadata {
        labels = {
          app = "vaspnestagent-backend"
        }
      }

      spec {
        service_account_name = kubernetes_service_account.vaspnestagent.metadata[0].name

        container {
          name  = "vaspnestagent"
          image = "${var.backend_image}:${var.backend_image_tag}"

          port {
            container_port = var.http_port
          }

          env_from {
            config_map_ref {
              name = kubernetes_config_map.vaspnestagent.metadata[0].name
            }
          }

          resources {
            requests = {
              memory = var.backend_memory_request
              cpu    = var.backend_cpu_request
            }
            limits = {
              memory = var.backend_memory_limit
              cpu    = var.backend_cpu_limit
            }
          }

          liveness_probe {
            http_get {
              path = "/health"
              port = var.http_port
            }
            initial_delay_seconds = 10
            period_seconds        = 30
            timeout_seconds       = 5
            failure_threshold     = 3
          }

          readiness_probe {
            http_get {
              path = "/ready"
              port = var.http_port
            }
            initial_delay_seconds = 5
            period_seconds        = 10
            timeout_seconds       = 3
            failure_threshold     = 3
          }
        }
      }
    }
  }
}

# Frontend Deployment
resource "kubernetes_deployment" "frontend" {
  metadata {
    name      = "vaspnestagent-frontend"
    namespace = kubernetes_namespace.vaspnestagent.metadata[0].name
    labels = {
      app = "vaspnestagent-frontend"
    }
  }

  spec {
    replicas = var.frontend_replicas

    selector {
      match_labels = {
        app = "vaspnestagent-frontend"
      }
    }

    template {
      metadata {
        labels = {
          app = "vaspnestagent-frontend"
        }
      }

      spec {
        container {
          name  = "frontend"
          image = "${var.frontend_image}:${var.frontend_image_tag}"

          port {
            container_port = 80
          }

          resources {
            requests = {
              memory = var.frontend_memory_request
              cpu    = var.frontend_cpu_request
            }
            limits = {
              memory = var.frontend_memory_limit
              cpu    = var.frontend_cpu_limit
            }
          }

          liveness_probe {
            http_get {
              path = "/"
              port = 80
            }
            initial_delay_seconds = 5
            period_seconds        = 30
          }

          readiness_probe {
            http_get {
              path = "/"
              port = 80
            }
            initial_delay_seconds = 3
            period_seconds        = 10
          }
        }
      }
    }
  }
}
