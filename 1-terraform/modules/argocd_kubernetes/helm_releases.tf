# ArgoCD
resource "helm_release" "argocd_base" {
  name       = "argocd-base"
  chart      = "${path.module}/../../../2-kubernetes/argocd-base"

  namespace = "argocd"
  create_namespace = true

  wait = true
  timeout = 1800

  max_history = 3

  set_sensitive {
    name  = "argo-cd.configs.secret.argocdServerAdminPassword"
    value = bcrypt(var.argocd_admin_password)
    type = "string"
  }

  set {
    name = "aws_account_id"
    value = var.aws_account_id
    type = "string"
  }

  set {
    name = "aws_region"
    value = var.aws_region
    type = "string"
  }

  set {
    name = "domain_name"
    value = var.domain_name
    type = "string"
  }

  set_sensitive {
    name = "github_app.private_key"
    value = var.github_app_private_key
    type = "string"
  }

  set_sensitive {
    name = "linkerd.certificate_authority_cert"
    value = var.certificate_authority_cert
    type = "string"
  }

  set_sensitive {
    name = "linkerd.issuer_cert"
    value = var.issuer_cert
    type = "string"
  }

  set_sensitive {
    name = "linkerd.issuer_private_key"
    value = var.issuer_key
    type = "string"
  }
}