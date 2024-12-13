resource "aws_eks_cluster" "cluster" {
    name = var.cluster_name
    role_arn = aws_iam_role.cluster_role.arn

    vpc_config {
        endpoint_public_access = true
        endpoint_private_access = true
        subnet_ids = [for s in data.aws_subnet.subnets : s.id]
    }

    depends_on = [
      aws_iam_role_policy_attachment.attach_policy_AmazonEKSClusterPolicy
    ]
}