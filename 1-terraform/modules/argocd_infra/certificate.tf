resource "aws_acm_certificate" "argocd" {
  domain_name       = aws_route53_record.argocd.name
  validation_method = "DNS"
}

resource "aws_acm_certificate_validation" "argocd" {
  certificate_arn         = aws_acm_certificate.argocd.arn
  validation_record_fqdns = [for record in aws_route53_record.argocd_validation : record.fqdn]

  lifecycle {
    ignore_changes = [ validation_record_fqdns ]
  }
}