data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

data "aws_route53_zone" "zone" {
    zone_id = var.zone_id
}