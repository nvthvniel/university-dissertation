resource "aws_eks_node_group" "cluster" {
    cluster_name = var.cluster_name
    node_group_name = "${var.cluster_name}-nodegroup"
    node_role_arn = aws_iam_role.node_group_role.arn
    subnet_ids = [for s in data.aws_subnet.subnets : s.id]

    scaling_config {
      desired_size = 3
      max_size     = 3
      min_size     = 3
    }

    depends_on = [
      aws_iam_role_policy_attachment.attach_policy_AmazonEKSWorkerNodePolicy,
      aws_iam_role_policy_attachment.attach_policy_AmazonEC2ContainerRegistryReadOnly,
      aws_iam_role_policy_attachment.attach_policy_AmazonEKS_CNI_Policy
    ]

    ami_type = "BOTTLEROCKET_x86_64"

    capacity_type = "ON_DEMAND"

    disk_size = "30"

    instance_types = ["t3.medium"]

    tags = {
      "cluster" = aws_eks_cluster.cluster.name
    }
}