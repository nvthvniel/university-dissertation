variable "argocd_admin_password" {
    description = "Password for admin user"
    type = string
    sensitive = true
}

variable "github_app_private_key" {
  description = "GitHub app's Private key"
  type = string
  sensitive = true
}

variable "aws_account_id" {
  description = "AWS Account ID housing resources"
  type = string
}

variable "aws_region" {
  description = "AWS region housing resources"
  type = string
}

variable "domain_name" {
  description = "Domain name to use for Route53 records"
  type = string
}

variable "certificate_authority_cert" {
  description = "Linkerd Certificate authority TLS certificate"
  type = string
}

variable "issuer_cert" {
  description = "Linkerd issuer TLS certificate"
  type = string
}

variable "issuer_key" {
  description = "Linkerd issuer private key"
  type = string
}

variable "cluster_name" {
  description = "Name of EKS cluster"
  type = string
}