output "cluster_endpoint" {
    value = aws_eks_cluster.cluster.endpoint
}

output "cluster_cert" {
    value = aws_eks_cluster.cluster.certificate_authority.0.data
}

output "cluster_name" {
    value = var.cluster_name
}

output "openid_connect_provider" {
    value = aws_iam_openid_connect_provider.cluster
}