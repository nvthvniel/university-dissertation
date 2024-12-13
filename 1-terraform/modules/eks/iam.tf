# Cluster role's trust relationship policy document
data "aws_iam_policy_document" "cluster_role_trust_relationship" {
    statement {
        effect = "Allow"

        principals {
        type        = "Service"
        identifiers = ["eks.amazonaws.com"]
        }

        actions = ["sts:AssumeRole"]
    }
}

# Role for cluster to assume
resource "aws_iam_role" "cluster_role" {
  name = "${var.cluster_name}-cluster-role"
  description = "Assumed by EKS cluster"
  assume_role_policy = data.aws_iam_policy_document.cluster_role_trust_relationship.json
}

# Attach arn:aws:iam::aws:policy/AmazonEKSClusterPolicy policy to role
resource "aws_iam_role_policy_attachment" "attach_policy_AmazonEKSClusterPolicy" {
    role = aws_iam_role.cluster_role.id
    policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
}





# Node group role's trust relationship policy document
data "aws_iam_policy_document" "node_group_role_trust_relationship" {
    statement {
        effect = "Allow"

        principals {
        type        = "Service"
        identifiers = ["ec2.amazonaws.com"]
        }

        actions = ["sts:AssumeRole"]
    }
}

# Role for node group to assume
resource "aws_iam_role" "node_group_role" {
  name = "${var.cluster_name}-nodegroup-role"
  description = "Assumed by EKS clusters nodes"
  assume_role_policy = data.aws_iam_policy_document.node_group_role_trust_relationship.json
}

# Attach arn:aws:iam::aws:policy/AmazonEKSClusterPolicy policy to role
resource "aws_iam_role_policy_attachment" "attach_policy_AmazonEKSWorkerNodePolicy" {
    role = aws_iam_role.node_group_role.id
    policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
}

# Attach arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly policy to role
resource "aws_iam_role_policy_attachment" "attach_policy_AmazonEC2ContainerRegistryReadOnly" {
    role = aws_iam_role.node_group_role.id
    policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

# Attach arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy policy to role
resource "aws_iam_role_policy_attachment" "attach_policy_AmazonEKS_CNI_Policy" {
    role = aws_iam_role.node_group_role.id
    policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
}