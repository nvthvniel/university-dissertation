output "argocd_service" {
    value = data.kubernetes_service.argocd_server.status.0.load_balancer.0.ingress.0.hostname
}

output "kourier_service" {
    value = data.kubernetes_service.kourier.status.0.load_balancer.0.ingress.0.hostname
}