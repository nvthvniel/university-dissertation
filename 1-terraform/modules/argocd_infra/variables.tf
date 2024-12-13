variable "argocd_service" {
  description = "Hostname of ArgoCD load balancer"
  type = string
}

variable "kourier_service" {
  description = "Hostname of Kourier load balancer"
  type = string
}

variable "aws_account_id" {
  description = "AWS account ID"
  type = string
}

variable "domain_name" {
  description = "Domain name to use for Route53 records"
  type = string
}

variable cluster_name {
    description = "Name of EKS cluster that will be built"
}

variable openid_connect_provider {
    description = "Name of EKS cluster that will be built"
}

variable ssm_parameters {
    description = "SSM parameter keys + values"
}
