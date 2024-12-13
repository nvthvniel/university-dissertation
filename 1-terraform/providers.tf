provider "aws" {
  
  region = "us-east-1"
}

# https://developer.hashicorp.com/terraform/tutorials/kubernetes/helm-provider#review-the-helm-configuration
provider "helm" {
  kubernetes {
    host                   = module.cluster.cluster_endpoint
    cluster_ca_certificate = base64decode(module.cluster.cluster_cert)

    exec {
      api_version = "client.authentication.k8s.io/v1beta1"
      args        = ["eks", "get-token", "--cluster-name", module.cluster.cluster_name]
      command     = "aws"
    }
  }
}

provider "kubernetes" {
  host                   = module.cluster.cluster_endpoint
  cluster_ca_certificate = base64decode(module.cluster.cluster_cert)

  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    args        = ["eks", "get-token", "--cluster-name", module.cluster.cluster_name]
    command     = "aws"
  }
}

provider "tls" {}