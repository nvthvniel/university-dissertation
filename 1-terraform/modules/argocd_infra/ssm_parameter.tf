resource "aws_ssm_parameter" "parameter" {
    for_each = {for item in var.ssm_parameters: item.key => item.value}

    name = each.key
    type = "SecureString"
    value = each.value
}