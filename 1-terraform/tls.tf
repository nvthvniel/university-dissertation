resource "tls_private_key" "certificate_authority" {
  algorithm   = "ECDSA"
  ecdsa_curve = "P256"
}

resource "tls_self_signed_cert" "certificate_authority" {
  private_key_pem = tls_private_key.certificate_authority.private_key_pem

  subject {
    common_name = "root.linkerd.cluster.local"
  }

  validity_period_hours = 24

  allowed_uses = [
    "cert_signing",
    "crl_signing"
  ]

  is_ca_certificate = true
}

resource "tls_private_key" "issuer" {
  algorithm   = "ECDSA"
  ecdsa_curve = "P256"
}


resource "tls_cert_request" "issuer" {
  private_key_pem = tls_private_key.issuer.private_key_pem

  subject {
    common_name = "identity.linkerd.cluster.local"
  }
}

resource "tls_locally_signed_cert" "issuer" {
  cert_request_pem   = tls_cert_request.issuer.cert_request_pem
  ca_private_key_pem = tls_private_key.certificate_authority.private_key_pem
  ca_cert_pem        = tls_self_signed_cert.certificate_authority.cert_pem

  validity_period_hours = 24

  allowed_uses = [
    "cert_signing",
    "crl_signing"
  ]

  is_ca_certificate = true
}