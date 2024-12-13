resource "aws_dynamodb_table" "jarvis_table" {
  name           = "jarvis"
  billing_mode   = "PROVISIONED"
  read_capacity  = 20
  write_capacity = 20
  hash_key       = "callback_id"

  attribute {
    name = "callback_id"
    type = "S"
  }

  ttl {
    attribute_name = "expire_at"
    enabled        = true
  }

  server_side_encryption {
    # Use AWS managed KMS customer master key: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/dynamodb_table#server_side_encryption
    enabled = false
  }
}