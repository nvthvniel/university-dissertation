# Defined in terraform.tfvars
variable "argocd_admin_password" {
  description = "Password for admin user"
  type        = string
  sensitive   = true
}

variable "github_app_private_key" {
  description = "GitHub app's Private key"
  type        = string
  sensitive   = true
}

variable "slack_signing_secret" {
  description = "Slack app's signing secret to authenticate received events"
  type      = string
  nullable  = false
  sensitive = true
}

variable "slack_api_token" {
  description = "Token to authenticate to Slack's API"
  type      = string
  nullable  = false
  sensitive = true
}

variable "chatgpt_api_token" {
  description = "Token to authenticate to OpenAI's API"
  type      = string
  nullable  = false
  sensitive = true
}

variable "dev_project_registry" {
  description = "Docker credentials to download container images"
  type      = string
  nullable  = false
  sensitive = true
}

variable "zone_id" {
  description = "ID of existing AWS Route53 Hosted Zone"
  type = string
}


# Configuration values
variable "cluster_name" {
  description = "Name of EKS cluster"
  type        = string
  default     = "jarvis"
}

variable "kubernetes_version" {
  description = "Version of Kubernetes to use. See https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html#available-versions"
  type        = string
  default     = "1.28"
}