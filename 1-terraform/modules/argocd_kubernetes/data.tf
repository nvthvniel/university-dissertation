data "kubernetes_service" "argocd_server" {
  metadata {
    name = "argocd-base-server"
    namespace = "argocd"
  }

  depends_on = [ 
    helm_release.argocd_base
  ]
}


data "kubernetes_service" "kourier" {
  metadata {
    name = "kourier"
    namespace = "knative-serving"
  }

  depends_on = [ 
    helm_release.argocd_base
  ]
}