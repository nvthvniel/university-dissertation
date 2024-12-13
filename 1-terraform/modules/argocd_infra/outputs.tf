output "argocd_url" {
    value = aws_route53_record.argocd.name
}
