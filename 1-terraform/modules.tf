# Builds EKS cluster
module "cluster" {
  source = "./modules/eks"

  cluster_name       = var.cluster_name
  kubernetes_version = var.kubernetes_version
}


# Installs + Configures ArgoCD
#  ArgoCD Base install
#  ArgoCD Project
#  GitHub Repository connection
#  App-of-apps appset
module "argocd_kubernetes" {
  source = "./modules/argocd_kubernetes"

  argocd_admin_password = var.argocd_admin_password

  github_app_private_key = var.github_app_private_key

  aws_account_id = data.aws_caller_identity.current.account_id
  aws_region     = data.aws_region.current.name
  domain_name    = trim(data.aws_route53_zone.zone.name, ".")
  cluster_name = module.cluster.cluster_name

  certificate_authority_cert = tls_self_signed_cert.certificate_authority.cert_pem
  issuer_cert                = tls_locally_signed_cert.issuer.cert_pem
  issuer_key                 = tls_private_key.issuer.private_key_pem

  depends_on = [module.cluster]
}


# Builds supporting infrastructure for kubernetes resources deployed via ArgoCD
#  Route53 records
#  TLS Certificates
#  IAM Roles
#  S3 Bucket
#  DynamoDB Table
#  SSM Parameters
module "argocd_infra" {
  source = "./modules/argocd_infra"

  argocd_service  = module.argocd_kubernetes.argocd_service
  kourier_service = module.argocd_kubernetes.kourier_service

  aws_account_id = data.aws_caller_identity.current.account_id
  domain_name    = trim(data.aws_route53_zone.zone.name, ".")

  cluster_name            = module.cluster.cluster_name
  openid_connect_provider = module.cluster.openid_connect_provider

  ssm_parameters = [
    {
      key   = "jarvis-slack-signing-secret",
      value = "{\"secret\": \"${var.slack_signing_secret}\"}"
    },
    {
      key   = "jarvis-slack-api-token",
      value = "{\"secret\": \"${var.slack_api_token}\"}"
    },
    {
      key   = "jarvis-chatgpt-api-token",
      value = "{\"secret\": \"${var.chatgpt_api_token}\"}"
    },
    {
      key   = "dev-project-registry",
      value = var.dev_project_registry
    }
  ]

  depends_on = [module.argocd_kubernetes]
}


# Builds infrastructure to demonstrate system's capabilities
#  EC2 instance x2
#  IAM Role + Policy
module "demo_resources" {
  source = "./modules/demo_resources"
}