data "aws_iam_policy_document" "demo_permission_policy" {

  statement {
    actions = ["*"]
    effect  = "Allow"
    resources = ["*"]
  }
}

resource "aws_iam_policy" "demo" {
  name        = "jarvis-demo"
  description = "Demo policy"
  policy      = data.aws_iam_policy_document.demo_permission_policy.json
}






resource "aws_iam_user" "demo_1" {
  name = "jarvis-demo-approval-needed"
  path = "/"

  tags = {
    jarvis-approval-required = "true"
  }
}

resource "aws_iam_user" "demo_2" {
  name = "jarvis-demo-no-approval"
  path = "/"

  tags = {
    jarvis-approval-required = "false"
  }
}

resource "aws_iam_access_key" "demo_1" {
  user = aws_iam_user.demo_2.name
}

resource "aws_iam_access_key" "demo_2" {
  user = aws_iam_user.demo_2.name
}

resource "aws_iam_user_policy" "demo_1" {
  name   = "jarvis-demo-user-1"
  user   = aws_iam_user.demo_1.name
  policy = data.aws_iam_policy_document.demo_permission_policy.json
}

resource "aws_iam_user_policy" "demo_2" {
  name   = "jarvis-demo-user-2"
  user   = aws_iam_user.demo_2.name
  policy = data.aws_iam_policy_document.demo_permission_policy.json
}








data "aws_iam_policy_document" "demo_role_trust_relationship" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "demo_1" {
  name               = "jarvis-demo-approval-needed"
  path               = "/"
  assume_role_policy = data.aws_iam_policy_document.demo_role_trust_relationship.json

  tags = {
    jarvis-approval-required = "true"
  }
}

resource "aws_iam_role" "demo_2" {
  name               = "jarvis-demo-no-approval"
  path               = "/"
  assume_role_policy = data.aws_iam_policy_document.demo_role_trust_relationship.json

  tags = {
    jarvis-approval-required = "false"
  }
}

resource "aws_iam_policy_attachment" "demo_1" {
  name = "jarvis-demo-role-1-attachement"
  roles = [aws_iam_role.demo_1.name]
  policy_arn = aws_iam_policy.demo.arn
}

resource "aws_iam_policy_attachment" "demo_2" {
  name = "jarvis-demo-role-2-attachement"
  roles = [aws_iam_role.demo_2.name]
  policy_arn = aws_iam_policy.demo.arn
}