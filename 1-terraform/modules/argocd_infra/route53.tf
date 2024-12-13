resource "aws_route53_record" "argocd" {
  zone_id = data.aws_route53_zone.zone.id
  name    = "argocd.${var.domain_name}"
  type    = "CNAME"
  ttl     = "300"
  records = [var.argocd_service]

  lifecycle {
    ignore_changes = [ zone_id, records ]
  }
}

resource "aws_route53_record" "argocd_validation" {
  for_each = {
    for dvo in aws_acm_certificate.argocd.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = data.aws_route53_zone.zone.zone_id

  lifecycle {
    ignore_changes = [ zone_id ]
  }
}

resource "aws_route53_record" "kourier" {
  zone_id = data.aws_route53_zone.zone.id
  name    = "*.knative.${var.domain_name}"
  type    = "CNAME"
  ttl     = "300"
  records = [var.kourier_service]

  lifecycle {
    ignore_changes = [ zone_id, records ]
  }
}
