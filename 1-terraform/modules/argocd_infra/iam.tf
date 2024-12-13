# external-secrets - SSM Parameter Store IAM Access
data "aws_iam_policy_document" "external_secret_trust_relationship" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    effect  = "Allow"

    condition {
      test     = "StringEquals"
      variable = "${replace(var.openid_connect_provider.url, "https://", "")}:sub"
      values   = ["system:serviceaccount:external-secrets:parameter-store-read"]
    }

    condition {
      test     = "StringEquals"
      variable = "${replace(var.openid_connect_provider.url, "https://", "")}:aud"
      values   = ["sts.amazonaws.com"]
    }

    principals {
      identifiers = [var.openid_connect_provider.arn]
      type        = "Federated"
    }
  }
}

resource "aws_iam_role" "external_secrets" {
  assume_role_policy = data.aws_iam_policy_document.external_secret_trust_relationship.json
  name               = "jarvis-external-secrets"
}


data "aws_iam_policy_document" "external_secret_permission_policy" {

  statement {
    actions = ["ssm:GetParameter"]
    effect  = "Allow"
    resources = values(aws_ssm_parameter.parameter)[*].arn
  }
}

resource "aws_iam_policy" "external_secrets" {
  name        = "jarvis-external-secrets"
  description = "Allows getting of parameter store values"
  policy      = data.aws_iam_policy_document.external_secret_permission_policy.json
}

resource "aws_iam_policy_attachment" "external_secrets" {
  name = "external-secrets-attachement"
  roles = [aws_iam_role.external_secrets.name]
  policy_arn = aws_iam_policy.external_secrets.arn
}



# jarvis - DynamoDB IAM Access
data "aws_iam_policy_document" "jarvis_dynamodb_access_trust_relationship" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    effect  = "Allow"

    condition {
      test     = "StringEquals"
      variable = "${replace(var.openid_connect_provider.url, "https://", "")}:sub"
      values   = ["system:serviceaccount:jarvis:dynamodb-access"]
    }

    condition {
      test     = "StringEquals"
      variable = "${replace(var.openid_connect_provider.url, "https://", "")}:aud"
      values   = ["sts.amazonaws.com"]
    }

    principals {
      identifiers = [var.openid_connect_provider.arn]
      type        = "Federated"
    }
  }
}

resource "aws_iam_role" "jarvis_dynamodb_access" {
  assume_role_policy = data.aws_iam_policy_document.jarvis_dynamodb_access_trust_relationship.json
  name               = "jarvis-dynamodb-access"
}

data "aws_iam_policy_document" "jarvis_dynamodb_access_permission_policy" {

  statement {
    actions = ["dynamodb:PutItem", "dynamodb:DeleteItem", "dynamodb:GetItem"]
    effect  = "Allow"
    resources = ["${aws_dynamodb_table.jarvis_table.arn}"]
  }
}

resource "aws_iam_policy" "jarvis_dynamodb_access" {
  name        = "jarvis-dynamodb-access"
  description = "Allows automation read and write access to dynamodb table"
  policy      = data.aws_iam_policy_document.jarvis_dynamodb_access_permission_policy.json
}

resource "aws_iam_policy_attachment" "jarvis_dynamodb_access" {
  name = "jarvis-dynamodb-access"
  roles = [aws_iam_role.jarvis_dynamodb_access.name]
  policy_arn = aws_iam_policy.jarvis_dynamodb_access.arn
}



# jarvis - S3 IAM Access
data "aws_iam_policy_document" "jarvis_s3_access_trust_relationship" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    effect  = "Allow"

    condition {
      test     = "StringEquals"
      variable = "${replace(var.openid_connect_provider.url, "https://", "")}:sub"
      values   = ["system:serviceaccount:jarvis:s3-access"]
    }

    condition {
      test     = "StringEquals"
      variable = "${replace(var.openid_connect_provider.url, "https://", "")}:aud"
      values   = ["sts.amazonaws.com"]
    }

    principals {
      identifiers = [var.openid_connect_provider.arn]
      type        = "Federated"
    }
  }
}

resource "aws_iam_role" "jarvis_s3_access" {
  assume_role_policy = data.aws_iam_policy_document.jarvis_s3_access_trust_relationship.json
  name               = "jarvis-s3-access"
}

data "aws_iam_policy_document" "jarvis_s3_access_permission_policy" {

  statement {
    actions = ["s3:PutObject"]
    effect  = "Allow"
    resources = ["${aws_s3_bucket.jarvis_bucket.arn}", "${aws_s3_bucket.jarvis_bucket.arn}/*"]
  }
}

resource "aws_iam_policy" "jarvis_s3_access" {
  name        = "jarvis-s3-access"
  description = "Allows automation write access to s3 bucket"
  policy      = data.aws_iam_policy_document.jarvis_s3_access_permission_policy.json
}

resource "aws_iam_policy_attachment" "jarvis_s3_access" {
  name = "jarvis-s3-access"
  roles = [aws_iam_role.jarvis_s3_access.name]
  policy_arn = aws_iam_policy.jarvis_s3_access.arn
}



# jarvis - ChatGPT helper
data "aws_iam_policy_document" "jarvis_chatgpt_helper_trust_relationship" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    effect  = "Allow"

    condition {
      test     = "StringEquals"
      variable = "${replace(var.openid_connect_provider.url, "https://", "")}:sub"
      values   = ["system:serviceaccount:jarvis:chatgpt-helper"]
    }

    condition {
      test     = "StringEquals"
      variable = "${replace(var.openid_connect_provider.url, "https://", "")}:aud"
      values   = ["sts.amazonaws.com"]
    }

    principals {
      identifiers = [var.openid_connect_provider.arn]
      type        = "Federated"
    }
  }
}

resource "aws_iam_role" "jarvis_chatgpt_helper" {
  assume_role_policy = data.aws_iam_policy_document.jarvis_chatgpt_helper_trust_relationship.json
  name               = "jarvis-chatgpt-helper"
}

data "aws_iam_policy_document" "jarvis_chatgpt_helper_permission_policy" {

  statement {
    actions = ["ec2:DescribeRegions"]
    effect  = "Allow"
    resources = ["*"]
  }
}

resource "aws_iam_policy" "jarvis_chatgpt_helper" {
  name        = "jarvis-chatgpt-helper"
  description = "Allows automation access to AWS environment to list available regions"
  policy      = data.aws_iam_policy_document.jarvis_chatgpt_helper_permission_policy.json
}

resource "aws_iam_policy_attachment" "jarvis_chatgpt_helper" {
  name = "jarvis-chatgpt-helper-attachment"
  roles = [aws_iam_role.jarvis_chatgpt_helper.name]
  policy_arn = aws_iam_policy.jarvis_chatgpt_helper.arn
}



# aws - Incident Response IAM Access
data "aws_iam_policy_document" "jarvis_irsa_trust_relationship" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    effect  = "Allow"

    condition {
      test     = "StringEquals"
      variable = "${replace(var.openid_connect_provider.url, "https://", "")}:sub"
      values   = ["system:serviceaccount:aws:jarvis-irsa"]
    }

    condition {
      test     = "StringEquals"
      variable = "${replace(var.openid_connect_provider.url, "https://", "")}:aud"
      values   = ["sts.amazonaws.com"]
    }

    principals {
      identifiers = [var.openid_connect_provider.arn]
      type        = "Federated"
    }
  }
}

resource "aws_iam_role" "jarvis_irsa" {
  assume_role_policy = data.aws_iam_policy_document.jarvis_irsa_trust_relationship.json
  name               = "jarvis-irsa"
}

data "aws_iam_policy_document" "jarvis_irsa_permission_policy" {

  statement {
    actions = ["sts:assumeRole"]
    effect  = "Allow"
    resources = ["arn:aws:iam::*:role/jarvis-incident-response"]
  }
}

resource "aws_iam_policy" "jarvis_irsa" {
  name        = "jarvis-irsa"
  description = "Allows automation access to AWS environment to conduct incident response actions"
  policy      = data.aws_iam_policy_document.jarvis_irsa_permission_policy.json
}

resource "aws_iam_policy_attachment" "jarvis_irsa" {
  name = "jarvis-irsa-attachment"
  roles = [aws_iam_role.jarvis_irsa.name]
  policy_arn = aws_iam_policy.jarvis_irsa.arn
}




data "aws_iam_policy_document" "jarvis_incident_response_trust_relationship" {
  statement {
    actions = ["sts:AssumeRole"]
    effect  = "Allow"

    principals {
      type        = "AWS"
      identifiers = ["${resource.aws_iam_role.jarvis_irsa.arn}"]
    }
  }
}

resource "aws_iam_role" "jarvis_incident_response" {
  assume_role_policy = data.aws_iam_policy_document.jarvis_incident_response_trust_relationship.json
  name               = "jarvis-incident-response"
}

data "aws_iam_policy_document" "jarvis_incident_response_permission_policy" {

  statement {
    actions = [
      "ec2:StopInstances", 
      "ec2:DescribeInstances",
      "ec2:CreateSecurityGroup",
      "ec2:ModifyInstanceAttribute",
      "ec2:RevokeSecurityGroupEgress",
      "ec2:CreateSnapshot",
      "ec2:CreateTags",
      "iam:ListUserTags",
      "iam:PutUserPolicy",
      "iam:ListRoleTags",
      "iam:PutRolePolicy",
      "iam:GetInstanceProfile"
    ]

    effect  = "Allow"
    resources = ["*"]
  }
}

resource "aws_iam_policy" "jarvis_incident_response" {
  name        = "jarvis-incident-response"
  description = "Allows automation access to AWS environment to conduct incident response actions"
  policy      = data.aws_iam_policy_document.jarvis_incident_response_permission_policy.json
}

resource "aws_iam_policy_attachment" "jarvis_incident_response" {
  name = "jarvis-incident-response-attachement"
  roles = [aws_iam_role.jarvis_incident_response.name]
  policy_arn = aws_iam_policy.jarvis_incident_response.arn
}