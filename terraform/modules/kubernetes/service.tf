# Kubernetes Services for vaspNestAgent

# Backend Service
resource "kubernetes_service" "backend" {
  metadata {
    name      = "vaspnestagent-backend"
    namespace = kubernetes_namespace.vaspnestagent.metadata[0].name
  }

  spec {
    selector = {
      app = "vaspnestagent-backend"
    }

    port {
      port        = var.http_port
      target_port = var.http_port
    }

    type = "ClusterIP"
  }
}

# Frontend Service
resource "kubernetes_service" "frontend" {
  metadata {
    name      = "vaspnestagent-frontend"
    namespace = kubernetes_namespace.vaspnestagent.metadata[0].name
  }

  spec {
    selector = {
      app = "vaspnestagent-frontend"
    }

    port {
      port        = 80
      target_port = 80
    }

    type = "ClusterIP"
  }
}

# Ingress
resource "kubernetes_ingress_v1" "main" {
  metadata {
    name      = "vaspnestagent-ingress"
    namespace = kubernetes_namespace.vaspnestagent.metadata[0].name
    annotations = {
      "kubernetes.io/ingress.class"                = "alb"
      "alb.ingress.kubernetes.io/scheme"           = "internet-facing"
      "alb.ingress.kubernetes.io/target-type"      = "ip"
      "alb.ingress.kubernetes.io/healthcheck-path" = "/health"
    }
  }

  spec {
    rule {
      http {
        path {
          path      = "/graphql"
          path_type = "Prefix"
          backend {
            service {
              name = kubernetes_service.backend.metadata[0].name
              port {
                number = var.http_port
              }
            }
          }
        }

        path {
          path      = "/health"
          path_type = "Prefix"
          backend {
            service {
              name = kubernetes_service.backend.metadata[0].name
              port {
                number = var.http_port
              }
            }
          }
        }

        path {
          path      = "/ready"
          path_type = "Prefix"
          backend {
            service {
              name = kubernetes_service.backend.metadata[0].name
              port {
                number = var.http_port
              }
            }
          }
        }

        path {
          path      = "/metrics"
          path_type = "Prefix"
          backend {
            service {
              name = kubernetes_service.backend.metadata[0].name
              port {
                number = var.http_port
              }
            }
          }
        }

        path {
          path      = "/"
          path_type = "Prefix"
          backend {
            service {
              name = kubernetes_service.frontend.metadata[0].name
              port {
                number = 80
              }
            }
          }
        }
      }
    }
  }
}
