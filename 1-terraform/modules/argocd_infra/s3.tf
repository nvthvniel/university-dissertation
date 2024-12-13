resource "aws_s3_bucket" "jarvis_bucket" {
  bucket = "jarvis-logs-${var.aws_account_id}"
}

resource "aws_s3_bucket_ownership_controls" "jarvis_bucket" {
  bucket = aws_s3_bucket.jarvis_bucket.id
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

# Force private access
resource "aws_s3_bucket_acl" "jarvis_bucket" {
  depends_on = [aws_s3_bucket_ownership_controls.jarvis_bucket]

  bucket = aws_s3_bucket.jarvis_bucket.id
  acl    = "private"
}

# Auto delete objects
resource "aws_s3_bucket_lifecycle_configuration" "jarvis_bucket" {
  bucket = aws_s3_bucket.jarvis_bucket.id

  rule {
    id = "delete"

    expiration {
      days = 60
    }

    # all objects
    filter {}

    status = "Enabled"
  }
}

# Force TLS
# Ref: https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements_condition_operators.html#Conditions_Boolean
data "aws_iam_policy_document" "jarvis_bucket" {
  statement {
    effect = "Deny"

    principals {
      type        = "AWS"
      identifiers = ["*"]
    }

    actions = ["s3:*"]

    resources = [
      aws_s3_bucket.jarvis_bucket.arn,
      "${aws_s3_bucket.jarvis_bucket.arn}/*",
    ]

    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}

resource "aws_s3_bucket_policy" "jarvis_bucket" {
  bucket = aws_s3_bucket.jarvis_bucket.id
  policy = data.aws_iam_policy_document.jarvis_bucket.json
}